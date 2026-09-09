import base64
import io
from ollama import chat
from PIL import ImageGrab

TEXT_MODEL   = "openbmb/minicpm5"
VISION_MODEL = "openbmb/minicpm-v4.6"

def grab_screen_b64(quality=70):
    shot = ImageGrab.grab()
    buf = io.BytesIO()
    shot.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()

def talk_text(prompt: str):
    r = chat(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.message.content

def talk_vision(prompt: str, image_b64: str = None):
    msg = {"role": "user", "content": prompt}
    if image_b64:
        msg["images"] = [image_b64]
    r = chat(model=VISION_MODEL, messages=[msg])
    return r.message.content

def main():
    print("Cinder dual-brain ready")
    print("  t  → talk to MiniCPM5 (text)")
    print("  v  → talk to MiniCPM-V 4.6 (vision)")
    print("  s  → ask vision about current screen")
    print("  q  → quit\n")

    while True:
        try:
            mode = input("mode [t/v/s/q]: ").strip().lower()
            if mode == "q":
                break
            if mode not in ("t", "v", "s"):
                print("unknown mode")
                continue

            prompt = input("you > ").strip()
            if not prompt:
                continue

            if mode == "t":
                print("\nMiniCPM5 >", talk_text(prompt), "\n")
            elif mode == "v":
                print("\nMiniCPM-V >", talk_vision(prompt), "\n")
            elif mode == "s":
                print("capturing screen…")
                img = grab_screen_b64()
                print("\nMiniCPM-V (screen) >", talk_vision(prompt, img), "\n")

        except KeyboardInterrupt:
            print("\nbye")
            break
        except Exception as e:
            print("error:", e)

if __name__ == "__main__":
    main()
