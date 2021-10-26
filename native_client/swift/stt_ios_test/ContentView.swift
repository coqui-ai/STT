//
//  ContentView.swift
//  stt_ios_test
//
//  Created by Reuben Morais on 15.06.20.
//  Copyright © 2020 Mozilla
//  Copyright © 2021 Coqui GmbH

import SwiftUI

struct ContentView: View {
    @State var isRecognizingMicrophone = false
    @State var partialResult = ""
    @State var result = ""
    @State var stt: SpeechRecognitionImpl? = nil

    func setup() {
        stt = SpeechRecognitionImpl(
            onPartialResult: { nextPartialResult in
                partialResult = nextPartialResult
            },
            onResult: { nextResult in
                result = nextResult
            }
        )
    }

    var body: some View {
        VStack {
            Text("Coqui STT iOS Demo")
                .font(.system(size: 30))

            if (stt != nil) {
                Button("Recognize files", action: recognizeFiles)
                    .padding(30)
                Button(
                    isRecognizingMicrophone
                        ? "Stop Microphone Recognition"
                        : "Start Microphone Recognition",
                    action: isRecognizingMicrophone
                        ? stopMicRecognition
                        : startMicRecognition)
                    .padding(30)
                Text("Partial result")
                Text(partialResult)
                Text("Result")
                Text(result)
            } else {
                Button("Setup", action: setup)
                    .padding(30)
            }
        }
    }

    func recognizeFiles() {
        stt?.recognizeFiles()
    }

    func startMicRecognition() {
        isRecognizingMicrophone = true
        stt?.startMicrophoneRecognition()
    }

    func stopMicRecognition() {
        isRecognizingMicrophone = false
        stt?.stopMicrophoneRecognition()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
