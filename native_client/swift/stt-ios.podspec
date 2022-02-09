# Pull in version from outside
version = File.read(File.join(__dir__, "../../training/coqui_stt_training/VERSION")).split("\n")[0]

Pod::Spec.new do |s|
  s.name         = "stt-ios"
  s.version      = version
  s.summary      = "Coqui STT"
  s.homepage     = "https://github.com/coqui-ai/STT"
  s.license      = "Mozilla Public License 2.0"
  s.authors      = "Coqui GmbH"

  s.platforms    = { :ios => "9.0" }
  s.source       = { :git => "https://github.com/coqui-ai/STT.git", :tag => "v#{s.version}" }

  # Assuming CI build location. Depending on your Xcode setup, this might be in
  # build/Release-iphoneos/stt_ios.framework instead.
  s.vendored_frameworks = "native_client/swift/DerivedData/Build/Products/Release-iphoneos/stt_ios.framework"
  s.source_files = "native_client/swift/stt_ios/**/*.{h,m,mm,swift}"
end
