import { useState, useEffect, useRef } from 'react';
import { X, Send, Plus, Trash2, Bot, User } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { storage, ChatSession, ChatMessage } from '../utils/mockData';
import { toast } from 'sonner';
import { getSessions, sendChatToBackend, startSession } from '../../services/api';

interface ChatbotProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Chatbot({ isOpen, onClose }: ChatbotProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const userId = user?._id;

  useEffect(() => {
  const init = async () => {
    const backendSessions = await getSessions();

    const formatted = backendSessions.map((s: any) => ({
      id: s._id,
      title: "Chat",
      messages: s.messages || [],
      createdAt: s.created_at,
    }));

    setSessions(formatted);

    if (formatted.length === 0) {
      const newSession = await startSession();
      setCurrentSessionId(newSession._id);
    } else {
      setCurrentSessionId(formatted[0].id);
    }
  };

  init();
}, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, currentSessionId]);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  const createNewChat = async () => {
  const newSession = await startSession();

  const formattedSession: ChatSession = {
    id: newSession._id,   // ✅ REAL DB ID
    title: "New Chat",
    messages: [],
    createdAt: new Date().toISOString(),
  };

  const newSessions = [formattedSession, ...sessions];
  setSessions(newSessions);
  setCurrentSessionId(newSession._id);

  toast.success('New chat created');
};

  const deleteChat = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const newSessions = sessions.filter(s => s.id !== id);
    setSessions(newSessions);

    if (currentSessionId === id && newSessions.length > 0) {
      setCurrentSessionId(newSessions[0].id);
    } else if (newSessions.length === 0) {
      createNewChat();
    }

    storage.setChatSessions(newSessions);
    toast.success('Chat deleted');
  };

  const sendMessage = async () => {
    if (!message.trim() || !currentSession) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };

    const updatedSession = {
      ...currentSession,
      messages: [...currentSession.messages, userMessage],
    };

    setSessions(sessions.map(s => s.id === currentSessionId ? updatedSession : s));
    setMessage('');
    setIsTyping(true);

    try {
      const res = await sendChatToBackend(message, currentSessionId!);
      console.log(res);
      const agentMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: typeof res.response === 'string'
        ? { message: res.response, products: [] }
        : {
            message: res.response?.message || 'No response',
            products: res.state?.recommended_items || [],
            prompt: res.response?.prompt || '',
          },
        timestamp: new Date().toISOString(),
      };

      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, agentMessage],
      };

      const newSessions = sessions.map(s => s.id === currentSessionId ? finalSession : s);
      setSessions(newSessions);
      storage.setChatSessions(newSessions);
    } catch {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        role: 'agent',
        content: 'Error connecting to server',
        timestamp: new Date().toISOString(),
      };

      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, errorMessage],
      };

      const newSessions = sessions.map(s => s.id === currentSessionId ? finalSession : s);
      setSessions(newSessions);
      storage.setChatSessions(newSessions);
    } finally {
      setIsTyping(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 md:p-4"
      onClick={onClose} // ✅ click outside closes
    >
      <Card
        className="w-full max-w-5xl h-[90vh] md:h-[600px] flex flex-col md:flex-row overflow-hidden"
        onClick={(e) => e.stopPropagation()} // ✅ prevent inside click
      >
        {/* Sidebar */}
        <div className="hidden md:flex md:w-64 border-r bg-muted/20 p-4 flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Chat History</h3>
            <Button size="icon" variant="ghost" onClick={createNewChat}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <ScrollArea className="flex-1 overflow-y-auto">
            <div className="space-y-2">
              {sessions.map(session => (
                <div
                  key={session.id}
                  onClick={() => setCurrentSessionId(session.id)}
                  className={`p-3 rounded-lg cursor-pointer flex justify-between ${
                    currentSessionId === session.id ? 'bg-muted' : ''
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{session.title}</p>
                  </div>
                  <Button size="icon" variant="ghost" onClick={(e) => deleteChat(session.id, e)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Main Chat */}
        <div className="flex-1 flex flex-col min-h-0"> {/* ✅ KEY FIX */}

          {/* Header */}
          <div className="p-4 border-b flex justify-between">
            <h2 className="font-semibold">AI Shopping Assistant</h2>
            <Button size="icon" variant="ghost" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              {currentSession?.messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {msg.role === 'agent' && <Bot className="mr-1" />}

                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
                      msg.role === 'user' ? 'bg-primary text-white' : 'bg-muted'
                    }`}
                  >
                    {/* 🔥 SMART RENDERING BACK */}
                    {msg.role === 'agent' && typeof msg.content === 'object' && msg.content !== null ? (
                      <div className="space-y-2">
                        {/* Message */}
                        <p className="text-sm">{(msg.content as any).message}</p>

                        {/* Products */}
                        {(msg.content as any).products?.length > 0 && (
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {(msg.content as any).products.map((p: any) => (
                              <Card
                                key={p.product_id}
                                className="p-2 flex flex-col items-center hover:shadow-md transition cursor-pointer"
                              >
                                <img
                                  src={p.image}
                                  className="w-20 h-20 object-cover rounded-md"
                                />
                                <p className="text-xs font-semibold text-center">
                                  {p.name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  ₹{p.price}
                                </p>
                              </Card>
                            ))}
                          </div>
                        )}

                        {/* Prompt */}
                        {(msg.content as any).prompt && (
                          <p className="text-xs italic text-gray-500">
                            {(msg.content as any).prompt}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm">
                        {typeof msg.content === 'string'
                          ? msg.content
                          : msg.content.message}
                      </p>
                    )}
                  </div>

                  {msg.role === 'user' && <User className="ml-1" />}
                </div>
              ))}

              {isTyping && <p className="text-sm">Typing...</p>}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage();
              }}
              className="flex space-x-2"
            >
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type message..."
              />
              <Button type="submit">
                <Send />
              </Button>
            </form>
          </div>

        </div>
      </Card>
    </div>
  );
}