import AVFAudio

class AudioInput {
    private let engine: AVAudioEngine = AVAudioEngine()
    private let converter: AVAudioConverter
    private let onData: (_ shorts: [Int16]) -> Void

    private let bus: Int = 0

    // Interval to determine the buffer size
    // regarding the input device's sample rate.
    private let processingIntervalInMillis = 200

    private var audioData: Data = Data()

    private let outputFormat = AVAudioFormat(
        commonFormat: AVAudioCommonFormat.pcmFormatInt16,
        sampleRate: 16000.0,
        channels: 1,
        interleaved: true
    )!

    init(onData: @escaping (_ shorts: [Int16]) -> Void) {
        self.onData = onData

        let inputFormat = engine.inputNode.outputFormat(forBus: bus)
        self.converter = AVAudioConverter(from: inputFormat, to: outputFormat)!

        engine.inputNode.installTap(
            onBus: bus,
            bufferSize: UInt32(Double(processingIntervalInMillis / 1000) * inputFormat.sampleRate),
            format: inputFormat,
            block: handleInput
        )
    }

    // inspired by https://stackoverflow.com/a/40823574/8170620
    private func handleInput(buffer: AVAudioPCMBuffer, time: AVAudioTime) {
        var newBufferAvailable = true

        let inputCallback: AVAudioConverterInputBlock = { inNumPackets, outStatus in
            if newBufferAvailable {
                outStatus.pointee = .haveData
                newBufferAvailable = false
                return buffer
            } else {
                outStatus.pointee = .noDataNow
                return nil
            }
        }

        let convertedBuffer = AVAudioPCMBuffer(
            pcmFormat: self.outputFormat,
            frameCapacity: AVAudioFrameCount(self.outputFormat.sampleRate) * buffer.frameLength / AVAudioFrameCount(buffer.format.sampleRate)
        )!

        var error: NSError?
        let status = converter.convert(to: convertedBuffer, error: &error, withInputFrom: inputCallback)
        assert(status != .error)

        let shorts = UnsafeBufferPointer(
            start: convertedBuffer.int16ChannelData!.pointee,
            count: Int(convertedBuffer.frameLength)
        )

        onData(Array(shorts))
    }

    func start() {
        engine.prepare()
        try! engine.start()
    }

    func stop() {
        engine.stop()
    }
}
