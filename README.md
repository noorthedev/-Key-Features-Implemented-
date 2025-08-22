# 🤖 Console-Based Support Agent System (OpenAI Agents SDK)

A console-based multi-agent customer support system built with the **OpenAI Agents SDK**.  
This project demonstrates how to design **agentic systems** that can route, handoff, and manage queries across specialized agents.  

---

## ✨ Features
- **Multi-Agent Setup**  
  - Triage Agent (routes queries)  
  - Billing Agent  
  - Technical Agent  
  - General Support Agent  

- **Agent Handoffs**  
  The Triage Agent automatically decides which agent should handle the query.  

- **Context Management**  
  Uses **Pydantic models** to store structured user info like:  
  - Name  
  - Premium Status  
  - Issue Type  

# 🤝 Contribution
I welcome contributions! Feel free to submit issues or pull requests.

# 📢 Connect
📧 Email: nanum3773@gmail.com

💼 LinkedIn: Anum Rajput

💻 GitHub: Anum Rajput

🐦 X (Twitter): @Anumrajput88

# ⭐ Star this repository if you find it inspiring!
Happy coding!
- **Dynamic Tool Gating**  
  Tools are only enabled when needed.  

- **Console Interaction**  
  Fully interactive CLI support simulation.  

- **Guardrails**  
  Stops agents from responding with restricted words/phrases.  

---

## 🛠 Tech Stack
- Python 3.10+  
- [OpenAI Agents SDK](https://github.com/openai)  
- Pydantic  

---

## ⚡ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/support-agent-system.git
   cd support-agent-system

2. Create & activate a virtual environment:

python -m venv .venv
source .venv/bin/activate   # On Linux/Mac
.venv\Scripts\activate      # On Windows


3. Install dependencies:

pip install openai pydantic

# ▶️ Usage

Run the console support agent system:

python main.py

# sreenshort 
<img width="1834" height="928" alt="image" src="https://github.com/user-attachments/assets/d577cd35-d694-43ae-af41-38ba1fd5d5c8" />

<img width="1878" height="915" alt="image" src="https://github.com/user-attachments/assets/4a3a281c-ce86-4b04-8f13-6da35662c380" />

# Example:

👋 Welcome to Support Agent System!
Enter your name: Noor
Are you a premium user? (yes/no): yes
Describe your issue: I need help with my billing

Triage Agent: I will connect you to the Billing Support Agent...
Billing Agent: Hello Noor, I see you're a premium user. Let's solve your billing issue!

# 📜 License

This project is licensed under the MIT License.

