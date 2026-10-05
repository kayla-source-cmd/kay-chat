"""Terminal chat for testing the brain. Run from the backend/ folder:  python chat_cli.py"""
from app.core.chat_engine import ChatEngine
from app.providers import get_provider
from app.providers.base import ProviderError


def main() -> None:
    try:
        provider = get_provider()
    except ProviderError as e:
        print(e)
        return

    engine = ChatEngine(provider)
    print(f"Kay-Chat is ready (using {provider.name}). Type 'new' for a fresh chat, 'exit' to quit.\n")

    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in {"exit", "quit"}:
            break
        if text.lower() == "new":
            engine.reset()
            print("Started a new chat.\n")
            continue

        print("Kay-Chat: ", end="", flush=True)
        try:
            for chunk in engine.reply(text):
                print(chunk, end="", flush=True)
        except ProviderError as e:
            print(f"\n[Error] {e}")
        print("\n")


if __name__ == "__main__":
    main()