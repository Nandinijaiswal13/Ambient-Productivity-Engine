# 🧠 Ambient Productivity Engine
### LLM-Driven Personal Productivity, Memory & Reflection System

## 📌 About the Project

**Ambient Productivity Engine** is an AI-powered personal productivity and reflection system designed to help individuals organise their daily activities, manage tasks, monitor goals, and understand their productivity patterns.

The system combines traditional productivity management with AI-driven memory retrieval. It maintains a record of user activities, goals, tasks, and reflections, allowing users to interact with their productivity history through an AI-powered conversational interface.

The key idea is to move beyond simply tracking what users do and help them understand what they have done, identify challenges, and make better decisions about their future activities.

## 🎯 Problem Statement

Traditional productivity applications primarily focus on task management, reminders, and activity tracking. However, they often provide limited support for understanding historical productivity patterns and learning from personal reflections.

Users need a system that not only records their daily progress but also makes their stored information accessible and useful.

**Our solution:** An intelligent productivity workspace that combines structured data management, vector-based memory retrieval, and Large Language Models to provide contextual productivity insights.

## ✨ Core Features

### 01. Productivity Dashboard
- Centralised overview of productivity information.
- Task completion statistics.
- Activity tracking and time summaries.
- Goal progress monitoring.

### 02. Smart Task Management
- Create and organise daily tasks.
- Assign priorities and deadlines.
- Monitor task completion status.
- Maintain task history.

### 03. Activity Tracking
- Record daily activities.
- Track time spent on individual activities.
- Maintain a historical activity log.
- Understand how time is distributed.

### 04. Goal Tracking
- Define personal and professional goals.
- Monitor progress towards objectives.
- Track completed and ongoing goals.

### 05. Daily Reflection
- Record daily experiences and reflections.
- Track energy levels.
- Document challenges and learning experiences.
- Maintain a history of personal reflections.

### 06. AI Memory Chat
An intelligent conversational interface that allows users to interact with their stored productivity information.

- Retrieve relevant historical activities and reflections.
- Answer questions using previously stored information.
- Identify recurring challenges.
- Generate contextual productivity suggestions.
- Support personalised, memory-based interactions.

## 🧰 Technology Stack

| Technology | Implementation |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive user interface |
| SQLite | Structured data persistence |
| ChromaDB | Vector-based memory storage |
| Ollama | Local Large Language Model execution |
| RAG | Contextual information retrieval |
| Sentence Transformers | Text embedding generation |
| all-MiniLM-L6-v2 | Semantic text embeddings |

## 🏗️ System Architecture

The project follows a modular architecture that separates user interaction, data storage, memory retrieval, and AI response generation.

### Application Workflow

```text
              USER
                |
                v
       STREAMLIT INTERFACE
                |
                v
       PYTHON APPLICATION
                |
        +-------+-------+
        |               |
        v               v
   SQLITE DATABASE   MEMORY SYSTEM
        |               |
        |               v
        |        TEXT EMBEDDINGS
        |               |
        |               v
        |           CHROMADB
        |               |
        +-------+-------+
                |
                v
          RAG PIPELINE
                |
                v
          OLLAMA LLM
                |
                v
       CONTEXTUAL RESPONSE
                |
                v
              USER
```

### How AI Memory Chat Works

1. **User Query:** The user asks a question about their productivity history.
2. **Embedding Generation:** The text is converted into a numerical vector using the sentence-transformer model.
3. **Memory Retrieval:** ChromaDB searches for semantically relevant stored information.
4. **Context Preparation:** Retrieved information is used as context for the language model.
5. **Response Generation:** Ollama generates a natural-language response based on the available context.
6. **Output:** The user receives a contextual answer or productivity recommendation.

## 🧠 Understanding the AI Components

**Retrieval-Augmented Generation (RAG)**

RAG combines information retrieval with language generation. Instead of relying only on the language model's general knowledge, the system retrieves relevant stored information to support its response.

**Vector Embeddings**

Embeddings represent text as numerical vectors. They help the system identify similarities between different sentences based on their meanings.

**ChromaDB**

ChromaDB is a vector database that stores embeddings and associated information, enabling semantic similarity searches.

**Ollama**

Ollama provides a way to run supported Large Language Models locally, allowing the application to generate AI responses without requiring every interaction to use an external cloud API.

## 📁 Project Structure

```text
ambient_productivity_engine/
│
├── app.py                 # Main Streamlit application
├── database.py            # SQLite database operations
├── llm.py                 # AI response generation
├── rag_memory.py          # Memory and RAG functionality
│
├── data/
│   ├── productivity.db    # Productivity database
│   └── chroma_memory/     # Vector memory storage
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 💬 Sample AI Memory Chat Queries

Try asking:

- What activities have I performed recently?
- What challenges have I mentioned in my previous reflections?
- Summarise my productivity history.
- What are my current goals and their progress?
- Which areas of my productivity need improvement?
- What should I prioritise based on my previous activities?

## 🚀 Future Scope

- Advanced productivity pattern analysis.
- More intelligent personalised recommendations.
- Voice-based interaction.
- Calendar and reminder integration.
- Improved long-term memory management.
- Multi-user productivity support.
- Enhanced AI-driven productivity predictions.



<p align="center">
  <strong>Built to make productivity more intelligent, reflective, and personalised. 🧠</strong>
</p>
