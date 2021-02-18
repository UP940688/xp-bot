#!/usr/bin/env python3
from sys import stderr
from bot import Bot


def main():
    b = Bot()
    try:
        b.run()
    except Exception as e:
        print(f"Bot Error: Crashed with the following exception: {e}", file=stderr)


if __name__ == "__main__":
    main()
