//
//  ContentView.swift
//  stt_ios_test
//
//  Created by Reuben Morais on 15.06.20.
//  Copyright © 2020 Mozilla
//  Copyright © 2021 Coqui GmbH

import SwiftUI

struct ContentView: View {
    private var stt = SpeechRecognitionImpl()
    @State var isRecognizingMicrophone = false

    var body: some View {
        VStack {
            Text("Coqui STT iOS Demo")
                .font(.system(size: 30))
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
        }
    }

    func recognizeFiles() {
        self.stt.recognizeFiles()
    }

    func startMicRecognition() {
        isRecognizingMicrophone = true
        self.stt.startMicrophoneRecognition()
    }

    func stopMicRecognition() {
        isRecognizingMicrophone = false
        self.stt.stopMicrophoneRecognition()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
