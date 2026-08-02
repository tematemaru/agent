class Verifier:
    def verify_write(self, actual: str, expected: str) -> bool:
        return actual == expected

    def verify_shell(self, result: dict) -> bool:
        return result.get("returncode") == 0