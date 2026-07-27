import AppKit
import AVFoundation
import CoreVideo
import ImageIO

let arguments = CommandLine.arguments
guard arguments.count >= 4 else {
    fputs("Usage: create_payrollminds_backup_walkthrough.swift OUTPUT.mov SECONDS_PER_SCENE IMAGE...\n", stderr)
    exit(2)
}

let outputURL = URL(fileURLWithPath: arguments[1])
guard let secondsPerScene = Int(arguments[2]), secondsPerScene > 0 else {
    fputs("SECONDS_PER_SCENE must be a positive integer.\n", stderr)
    exit(2)
}
let imageURLs = arguments.dropFirst(3).map { URL(fileURLWithPath: $0) }

func imageSize(_ url: URL) -> (Int, Int)? {
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
          let width = properties[kCGImagePropertyPixelWidth] as? Int,
          let height = properties[kCGImagePropertyPixelHeight] as? Int else {
        return nil
    }
    return (width, height)
}

guard let (width, height) = imageSize(imageURLs[0]) else {
    fputs("Unable to inspect the first screenshot.\n", stderr)
    exit(1)
}
try? FileManager.default.removeItem(at: outputURL)
let writer = try AVAssetWriter(outputURL: outputURL, fileType: .mov)
let videoInput = AVAssetWriterInput(
    mediaType: .video,
    outputSettings: [
        AVVideoCodecKey: AVVideoCodecType.h264,
        AVVideoWidthKey: width,
        AVVideoHeightKey: height,
    ]
)
let adaptor = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: videoInput,
    sourcePixelBufferAttributes: [
        kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
        kCVPixelBufferWidthKey as String: width,
        kCVPixelBufferHeightKey as String: height,
    ]
)
guard writer.canAdd(videoInput) else {
    fputs("Unable to add video input.\n", stderr)
    exit(1)
}
writer.add(videoInput)
guard writer.startWriting() else {
    fputs("Unable to start video writer: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
    exit(1)
}
writer.startSession(atSourceTime: .zero)

let framesPerSecond: CMTimeScale = 30
let framesPerScene = Int64(secondsPerScene) * Int64(framesPerSecond)
var frameIndex: Int64 = 0

for imageURL in imageURLs {
    guard let source = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fputs("Unable to load \(imageURL.path).\n", stderr)
        exit(1)
    }
    for _ in 0..<framesPerScene {
        while !videoInput.isReadyForMoreMediaData {
            Thread.sleep(forTimeInterval: 0.01)
        }
        var pixelBuffer: CVPixelBuffer?
        CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pixelBuffer)
        guard let buffer = pixelBuffer else {
            fputs("Unable to create a video frame.\n", stderr)
            exit(1)
        }
        CVPixelBufferLockBaseAddress(buffer, [])
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let context = CGContext(
            data: CVPixelBufferGetBaseAddress(buffer),
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
        )!
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        CVPixelBufferUnlockBaseAddress(buffer, [])
        let presentationTime = CMTime(value: frameIndex, timescale: framesPerSecond)
        guard adaptor.append(buffer, withPresentationTime: presentationTime) else {
            fputs("Unable to append video frame: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
            exit(1)
        }
        frameIndex += 1
    }
}

videoInput.markAsFinished()
let completion = DispatchSemaphore(value: 0)
writer.finishWriting { completion.signal() }
completion.wait()
guard writer.status == .completed else {
    fputs("Video writer failed: \(writer.error?.localizedDescription ?? "unknown error")\n", stderr)
    exit(1)
}
print("Created \(outputURL.path) with \(Double(frameIndex) / Double(framesPerSecond)) seconds of synthetic presenter scenes.")
