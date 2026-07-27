import AppKit
import AVFoundation

let arguments = CommandLine.arguments
guard arguments.count == 3 else {
    fputs("Usage: validate_payrollminds_backup_walkthrough.swift INPUT.mov OUTPUT_DIRECTORY\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: arguments[1])
let outputDirectory = URL(fileURLWithPath: arguments[2], isDirectory: true)
try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)

let asset = AVURLAsset(url: inputURL)
let duration = asset.duration
guard duration.isValid, duration.seconds > 0 else {
    fputs("The backup walkthrough has no playable duration.\n", stderr)
    exit(1)
}

let frameGenerator = AVAssetImageGenerator(asset: asset)
frameGenerator.appliesPreferredTrackTransform = true
let frameTimes: [(String, CMTime)] = [
    ("backup-start.png", .zero),
    ("backup-end.png", CMTime(seconds: max(duration.seconds - 0.25, 0), preferredTimescale: 600)),
]

for (name, time) in frameTimes {
    let image = try frameGenerator.copyCGImage(at: time, actualTime: nil)
    let representation = NSBitmapImageRep(cgImage: image)
    guard let png = representation.representation(using: .png, properties: [:]) else {
        fputs("Unable to encode \(name).\n", stderr)
        exit(1)
    }
    try png.write(to: outputDirectory.appendingPathComponent(name))
}

let formattedDuration = String(format: "%.1f", duration.seconds)
print("Validated \(inputURL.path): \(formattedDuration) seconds; start and end frames extracted.")
