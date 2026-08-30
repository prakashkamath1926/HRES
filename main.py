from dotenv import load_dotenv
import os

from services.fortyguard import submit_heatmap, wait_for_heatmap


load_dotenv()

api_key = os.getenv("FORTYGUARD_API_KEY")

print("HRES - Heat Response Emergency System")
print("API key loaded:", api_key is not None)


activity_id = submit_heatmap(api_key)

print("Activity ID:", activity_id)


result = wait_for_heatmap(
    api_key,
    activity_id
)


if result is not None:

    print("Heatmap Result:")
    print(result)

else:

    print("No heatmap result was generated.")