import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from image_provenance import inspect  # noqa: E402


def png(extra_chunks=()):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    body = chunk(b"IHDR", ihdr) + b"".join(chunk(k, d) for k, d in extra_chunks) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + body


class ImageProvenanceTest(unittest.TestCase):
    def check(self, data, suffix):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ("img" + suffix)
            p.write_bytes(data)
            return inspect(p)

    def test_generator_manifest_in_png_is_flagged(self):
        manifest = b"jumb c2pa c2pa.actions c2pa.created softwareAgent gpt-image digitalSourceType trainedAlgorithmicMedia"
        r = self.check(png([(b"caBX", manifest)]), ".png")
        self.assertTrue(r["c2pa_manifest_present"])
        self.assertEqual(["trainedAlgorithmicMedia"], r["digital_source_type"])
        self.assertIn("gpt-image", r["generator_hints"])
        self.assertEqual("GENERATED_LABELLED", r["verdict"])

    def test_plain_png_is_only_no_label_found(self):
        r = self.check(png(), ".png")
        self.assertEqual("NO_LABEL_FOUND", r["verdict"])
        self.assertIn("not proof", r["limits"])

    def test_xmp_composite_source_type_in_jpeg_is_flagged_without_manifest(self):
        xmp = b'<x:xmpmeta><rdf:Description Iptc4xmpExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia"/></x:xmpmeta>'
        data = b"\xff\xd8\xff\xe1" + struct.pack(">H", len(xmp) + 2) + xmp + b"\xff\xd9"
        r = self.check(data, ".jpg")
        self.assertEqual(["compositeWithTrainedAlgorithmicMedia"], r["digital_source_type"])
        self.assertEqual("GENERATED_LABELLED", r["verdict"])

    def test_manifest_without_generator_signal_is_not_called_generated(self):
        # A C2PA manifest from a camera or editor is provenance, not a generation label.
        r = self.check(png([(b"caBX", b"jumb c2pa c2pa.actions c2pa.opened softwareAgent CameraApp")]), ".png")
        self.assertTrue(r["c2pa_manifest_present"])
        self.assertEqual("NO_LABEL_FOUND", r["verdict"])


if __name__ == "__main__":
    unittest.main()
