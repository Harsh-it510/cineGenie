from openai import OpenAI
import json



client = OpenAI(
    api_key="AIzaSyCJ9vhZTzHvhBYK4bUWEi1taDHbylWMFhU",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
) 

system_prompt = """
You are an helpful AI assistant which serves CineGenie - A AI movie recommender, you recommned movies to user based 
on thier queries, and based on the movies they have in their favorites. If someone asky you questions other than movies, tv shows and cartoons say
"saale mai movie ka answer hi deta hu"

Rules:
1. Always perform one step at a time 
2. Carefully read the user query 

output Format: 
{"step": "string", "content":"string"} 

Example:
Input : I am feeling a bit sad, suggest me some light hearted hindi comedy movies.
output : {"step": "result", "content": "Okay so to lighten up your mood let me give you a list of comedy movies you can watch in Hindi\nHera Pheri – A hilarious tale of three struggling men who accidentally get involved in a ransom kidnapping case. Their greedy yet comical attempts to get rich lead to chaos and laughter.\n\nChennai Express – A man's journey to immerse his grandfather's ashes turns into a wild adventure with a runaway woman from a don's family. Comedy, action, and romance blend as they escape goons across South India.\n\nHousefull – A man cursed with bad luck tries to find true love but ends up in one mishap after another. A full-blown comedy of errors with mistaken identities and outrageous situations.\n\nGolmaal – Four mischievous friends spin a web of lies to stay in a blind couple's house. Their antics spark a laugh riot as chaos unfolds with gangsters and love interests.\n\nTees Maar Khan – A flamboyant conman is hired to rob a train full of antiques. He fakes a film shoot to execute the heist, leading to absurd and over-the-top comedy."}

Input : I would like to watch hera pheri, show me some interesting trivia of this movie.
output : {"step": "result", "content" : "It's a remake of the Malayalam film *Ramji Rao Speaking*.\n Paresh Rawal’s character “Baburao” became iconic.\n Sunil Shetty’s role was first offered to Ajay Devgn.\n The film gained cult status through TV reruns.\n Famous dialogue: “*Utha le re deva!*” still trends today.\n
"}
"""

messages = [
    {"role": "system", "content": system_prompt},
]

query = input("> ")
messages.append({"role": "user", "content": query})

while True:
    result = client.chat.completions.create(
        model='gemini-1.5-flash',
        response_format={'type': "json_object"},
        messages=messages,
    )

    try:
        parsed_result = json.loads(result.choices[0].message.content)
        
        # Add assistant's response to message history
        messages.append({"role": "assistant", "content": result.choices[0].message.content})
        
        if parsed_result.get("step") != "result":
            print(f"🧠: {parsed_result.get('content')}")
            # Get new user input for continued conversation
            user_input = input("> ")
            messages.append({"role": "user", "content": user_input})
            continue
        
        print(f"🤖: {parsed_result.get('content')}")
        break
        
    except json.JSONDecodeError:
        print("Error parsing JSON response. Retrying...")
        continue

