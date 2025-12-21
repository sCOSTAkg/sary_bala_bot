import asyncio
import os
from dotenv import load_dotenv
from services.gemini_service import gemini_service

async def check():
    print("🤖 --- STARTING DIAGNOSTICS ---")
    
    # 1. Check Env
    load_dotenv()
    if not os.getenv("BOT_TOKEN"):
        print("❌ Error: BOT_TOKEN is missing")
    else:
        print("✅ BOT_TOKEN found")
        
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY is missing")
    else:
        print("✅ GEMINI_API_KEY found")

    # 2. Check Gemini Service (Streaming)
    print("\n🧠 Checking Gemini Brain (Stream).")
    try:
        final_text = ""
        async for chunk in gemini_service.generate_response_stream(
            user_id=12345, # Test User
            prompt="Привет! Это тест. Ответь одним словом 'Работаю'."
        ):
            final_text = chunk # Chunk is usually full text or partial, logic depends on implementation
            # In my implementation, chunk is accumulative text
            pass
            
        print(f"✅ Gemini Response: {final_text}")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")

    # 3. Check Tools (Calculator)
    print("\n🛠 Checking Tools (Calculator)...")
    try:
        from services.tools_service import tools_service
        calc = tools_service.get_tools_for_gemini(["calculator"])[0]
        res = calc("2 + 2")
        print(f"✅ Calculator Result (2+2): {res}")
    except Exception as e:
        print(f"❌ Tools Error: {e}")

    print("\n--- DIAGNOSTICS COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(check())