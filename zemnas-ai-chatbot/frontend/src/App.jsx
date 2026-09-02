import { useState } from "react";
import "./index.css";

const API_URL = "http://127.0.0.1:8000/api/v1/chat";


function createSessionId() {
  return crypto.randomUUID();
}


function App() {

  const [sessionId, setSessionId] = useState(() => {

    const savedSession = localStorage.getItem(
      "zemnas_session_id"
    );

    if (savedSession) {
      return savedSession;
    }

    const newSessionId = createSessionId();

    localStorage.setItem(
      "zemnas_session_id",
      newSessionId
    );

    return newSessionId;
  });


  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 Welcome to Zemnas. How can I help you today?",
    },
  ]);


  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);


  const sendMessage = async () => {

    if (!input.trim() || loading) {
      return;
    }


    const userMessage = {
      role: "user",
      content: input.trim(),
    };


    setMessages((previous) => [
      ...previous,
      userMessage,
    ]);


    setInput("");

    setLoading(true);


    try {

      const response = await fetch(
        API_URL,
        {

          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({

            session_id: sessionId,

            message: userMessage.content,

          }),

        }
      );


      if (!response.ok) {

        throw new Error(
          "Failed to get response from server"
        );

      }


      const data = await response.json();


      const assistantMessage = {

        role: "assistant",

        content:
          data.response ||
          "Sorry, I couldn't understand that.",

      };


      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);


    } catch (error) {

      console.error(error);


      setMessages((previous) => [

        ...previous,

        {

          role: "assistant",

          content:
            "⚠️ Unable to connect to the chatbot server. Please make sure the backend is running.",

        },

      ]);

    } finally {

      setLoading(false);

    }

  };


  const handleKeyDown = (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      sendMessage();

    }

  };


  const clearChat = () => {

    const newSessionId =
      createSessionId();


    setSessionId(
      newSessionId
    );


    localStorage.setItem(
      "zemnas_session_id",
      newSessionId
    );


    setMessages([
      {
        role: "assistant",
        content:
          "Hello! 👋 Welcome to Zemnas. How can I help you today?",
      },
    ]);

  };


  return (

    <div className="app">

      <div className="chat-container">


        {/* HEADER */}

        <div className="chat-header">

          <div>

            <h2>
              Zemnas AI Assistant
            </h2>

            <p>
              Digital Solutions & IT Services
            </p>

          </div>


          <button
            className="clear-button"
            onClick={clearChat}
          >

            New Chat

          </button>

        </div>


        {/* CHAT MESSAGES */}

        <div className="messages">

          {messages.map(
            (message, index) => (

              <div
                key={index}
                className={
                  `message-row ${message.role}`
                }
              >

                <div className="message">

                  {message.content}

                </div>

              </div>

            )
          )}


          {loading && (

            <div className="message-row assistant">

              <div className="message typing">

                Typing...

              </div>

            </div>

          )}

        </div>


        {/* INPUT */}

        <div className="input-area">

          <textarea

            value={input}

            onChange={(event) =>
              setInput(
                event.target.value
              )
            }

            onKeyDown={
              handleKeyDown
            }

            placeholder="Type your message..."

            rows="1"

          />


          <button

            onClick={
              sendMessage
            }

            disabled={
              loading ||
              !input.trim()
            }

          >

            Send

          </button>

        </div>


      </div>

    </div>

  );

}


export default App;