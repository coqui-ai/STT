//
//  SpeechRecognitionImpl.swift
//  stt_ios_test
//
//  Created by Erik Ziegler on 27.07.20.
//  Copyright © 2020 Mozilla
//  Copyright © 2020 Erik Ziegler
//  Copyright © 2021 Coqui GmbH
import Foundation
import AVFoundation
import Accelerate

import stt_ios

class SpeechRecognitionImpl {
    private var model: STTModel
    private var stream: STTStream?

    private let modelFeedInterval = 0.1

    private var audioData = Data()
    private var timer: Timer? = nil
    private var audioInput: AudioInput? = nil
    private var bufferQueue: [[Int16]] = [[Int16]]()

    init() {
        let modelPath = Bundle.main.path(forResource: "model", ofType: "tflite")!
        let scorerPath = Bundle.main.path(forResource: "huge-vocab", ofType: "scorer")!

        model = try! STTModel(modelPath: modelPath)
        try! model.enableExternalScorer(scorerPath: scorerPath)
    }

    public func startMicrophoneRecognition() {
        audioData = Data()
        stream = try! model.createStream()

        audioInput = AudioInput() { shorts in
            self.bufferQueue.append(shorts)
        }

        print("Started listening...")
        audioInput!.start()

        timer = Timer.scheduledTimer(
            withTimeInterval: modelFeedInterval,
            repeats: true
        ) { _ in
            if (!self.bufferQueue.isEmpty) {
                let shorts = self.bufferQueue.removeFirst()
                self.stream!.feedAudioContent(buffer: shorts)

                // (optional) get partial result
                let partialResult = self.stream!.intermediateDecode()
                print(partialResult)

                // (optional) collect audio data for writing to file
                shorts.withUnsafeBufferPointer { buffPtr in
                    self.audioData.append(buffPtr)
                }
            }
        }
    }

    public func stopMicrophoneRecognition() {
        audioInput!.stop()

        timer!.invalidate()
        timer = nil
        bufferQueue.removeAll()

        let result = stream?.finishStream() ?? ""
        print("Result: " + result)

        // (optional) useful for checking the recorded audio
        writeAudioDataToPCMFile()
    }

    private func writeAudioDataToPCMFile() {
        let documents = NSSearchPathForDirectoriesInDomains(FileManager.SearchPathDirectory.documentDirectory, FileManager.SearchPathDomainMask.userDomainMask, true)[0]
        let filePath = documents + "/recording.pcm"
        let url = URL(fileURLWithPath: filePath)
        try! audioData.write(to: url)
        print("Saved audio to " + filePath)
    }

    // MARK: Audio file recognition

    private func render(audioContext: AudioContext?, stream: STTStream) {
        guard let audioContext = audioContext else {
            fatalError("Couldn't create the audioContext")
        }

        let sampleRange: CountableRange<Int> = 0..<audioContext.totalSamples

        guard let reader = try? AVAssetReader(asset: audioContext.asset)
            else {
                fatalError("Couldn't initialize the AVAssetReader")
        }

        reader.timeRange = CMTimeRange(start: CMTime(value: Int64(sampleRange.lowerBound), timescale: audioContext.asset.duration.timescale),
                                       duration: CMTime(value: Int64(sampleRange.count), timescale: audioContext.asset.duration.timescale))

        let outputSettingsDict: [String : Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsNonInterleaved: false
        ]

        let readerOutput = AVAssetReaderTrackOutput(track: audioContext.assetTrack,
                                                    outputSettings: outputSettingsDict)
        readerOutput.alwaysCopiesSampleData = false
        reader.add(readerOutput)

        var sampleBuffer = Data()

        // 16-bit samples
        reader.startReading()
        defer { reader.cancelReading() }

        while reader.status == .reading {
            guard let readSampleBuffer = readerOutput.copyNextSampleBuffer(),
                let readBuffer = CMSampleBufferGetDataBuffer(readSampleBuffer) else {
                    break
            }
            // Append audio sample buffer into our current sample buffer
            var readBufferLength = 0
            var readBufferPointer: UnsafeMutablePointer<Int8>?
            CMBlockBufferGetDataPointer(readBuffer,
                                        atOffset: 0,
                                        lengthAtOffsetOut: &readBufferLength,
                                        totalLengthOut: nil,
                                        dataPointerOut: &readBufferPointer)
            sampleBuffer.append(UnsafeBufferPointer(start: readBufferPointer, count: readBufferLength))
            CMSampleBufferInvalidate(readSampleBuffer)

            let totalSamples = sampleBuffer.count / MemoryLayout<Int16>.size
            print("read \(totalSamples) samples")

            sampleBuffer.withUnsafeBytes { (samples: UnsafeRawBufferPointer) in
                let unsafeBufferPointer = samples.bindMemory(to: Int16.self)
                stream.feedAudioContent(buffer: unsafeBufferPointer)
            }

            sampleBuffer.removeAll()
        }

        // if (reader.status == AVAssetReaderStatusFailed || reader.status == AVAssetReaderStatusUnknown)
        guard reader.status == .completed else {
            fatalError("Couldn't read the audio file")
        }
    }

    private func recognizeFile(audioPath: String, completion: @escaping () -> ()) {
        let url = URL(fileURLWithPath: audioPath)

        let stream = try! model.createStream()
        print("\(audioPath)")
        let start = CFAbsoluteTimeGetCurrent()
        AudioContext.load(fromAudioURL: url, completionHandler: { audioContext in
            guard let audioContext = audioContext else {
                fatalError("Couldn't create the audioContext")
            }
            self.render(audioContext: audioContext, stream: stream)
            let result = stream.finishStream()
            let end = CFAbsoluteTimeGetCurrent()
            print("\"\(audioPath)\": \(end - start) - \(result)")
            completion()
        })
    }

    public func recognizeFiles() {
        // Add file names (without extension) here if you want to test recognition from files.
        // Remember to add them to the project under Copy Bundle Resources.
        let files: [String] = []

        let serialQueue = DispatchQueue(label: "serialQueue")
        let group = DispatchGroup()
        group.enter()

        if let first = files.first {
            serialQueue.async {
                self.recognizeFile(audioPath: Bundle.main.path(forResource: first, ofType: "wav")!) {
                    group.leave()
                }
            }
        }

        for path in files.dropFirst() {
            group.wait()
            group.enter()
            self.recognizeFile(audioPath: Bundle.main.path(forResource: path, ofType: "wav")!) {
                group.leave()
            }
        }
    }
}
