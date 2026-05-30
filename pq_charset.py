from pathlib import Path
import tomllib  # Python 3.11+

class PQ_Charset:
    def __init__(self, path: str | Path):
        spec = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        self.decode_map: dict[int, str] = {}
        self.encode_map: dict[str, int] = {}

        for r in spec.get("ranges", []):
            custom_start = int(r["custom_start"], 16)
            custom_end = custom_start+int(r["custom_size"], 16)
            sjis_start = int(r["sjis_start"], 16)

            for custom_code in range(custom_start, custom_end + 1):
                offset = custom_code - custom_start
                sjis_code = sjis_start + offset
                sjis_bytes = sjis_code.to_bytes(2, "big")

                try:
                    char = sjis_bytes.decode("shift_jis")
                except UnicodeDecodeError:
                    continue

                self.decode_map[custom_code] = char
                self.encode_map[char] = custom_code

        for m in spec.get("mappings", []):
            code = int(m["code"], 16)
            char = m["char"]

            self.decode_map[code] = char
            self.encode_map[char] = code

    def decode(self, data: bytes) -> str:
        if len(data) % 2:
            raise ValueError("Input length must be divisible by 2")

        result = []

        for i in range(0, len(data), 2):
            code = int.from_bytes(data[i:i + 2], "big")
            try:
                result.append(self.decode_map[code])
            except KeyError:
                raise UnicodeDecodeError(
                    "custom-fixed2",
                    data,
                    i,
                    i + 2,
                    f"unknown code 0x{code:04X}",
                )

        return "".join(result)

    def encode(self, text: str) -> bytes:
        result = bytearray()

        for i, char in enumerate(text):
            try:
                code = self.encode_map[char]
            except KeyError:
                raise UnicodeEncodeError(
                    "custom-fixed2",
                    text,
                    i,
                    i + 1,
                    f"unknown char {char!r}",
                )

            result.extend(code.to_bytes(2, "big"))

        return bytes(result)