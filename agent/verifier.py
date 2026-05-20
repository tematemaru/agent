class Verifier:
    def verify_write(self, fs, path: str, expected: str):
        actual = fs.read_file(path)

        return actual == expected

    def verify_shell(self, result: dict):
        return result["returncode"] == 0