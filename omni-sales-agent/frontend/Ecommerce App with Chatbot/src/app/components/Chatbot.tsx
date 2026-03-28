import { useState, useEffect, useRef } from 'react';
import { X, Send, Plus, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { storage, getAgentResponse, ChatSession, ChatMessage } from '../utils/mockData';
import { toast } from 'sonner';

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

  useEffect(() => {
    const savedSessions = storage.getChatSessions();
    setSessions(savedSessions);
    if (savedSessions.length === 0) {
      createNewChat();
    } else {
      setCurrentSessionId(savedSessions[0].id);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, currentSessionId]);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  const createNewChat = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: `Chat ${sessions.length + 1}`,
      messages: [{
        id: '1',
        role: 'agent',
        content: 'Hello! I\'m your AI shopping assistant. I can help you with orders, products, shipping, returns, and more. How can I assist you today?',
        timestamp: new Date().toISOString(),
      }],
      createdAt: new Date().toISOString(),
    };
    const newSessions = [newSession, ...sessions];
    setSessions(newSessions);
    setCurrentSessionId(newSession.id);
    storage.setChatSessions(newSessions);
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

    // Simulate agent thinking
    setTimeout(() => {
      const agentMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: getAgentResponse(message),
        timestamp: new Date().toISOString(),
      };

      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, agentMessage],
      };

      const newSessions = sessions.map(s => s.id === currentSessionId ? finalSession : s);
      setSessions(newSessions);
      storage.setChatSessions(newSessions);
      setIsTyping(false);
    }, 1000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-2 md:p-4">
      <Card className="w-full max-w-5xl h-[90vh] md:h-[600px] flex flex-col md:flex-row overflow-hidden">
        {/* Sidebar - Chat History (Desktop) */}
        <div className="hidden md:flex md:w-64 border-r bg-muted/20 p-4 flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Chat History</h3>
            <Button size="icon" variant="ghost" onClick={createNewChat}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <ScrollArea className="flex-1">
            <div className="space-y-2">
              {sessions.map(session => (
                <div
                  key={session.id}
                  onClick={() => setCurrentSessionId(session.id)}
                  className={`p-3 rounded-lg cursor-pointer hover:bg-muted transition-colors flex items-center justify-between ${
                    currentSessionId === session.id ? 'bg-muted' : ''
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm truncate">{session.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(session.createdAt).toLocaleDateString()}
                    </p>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8"
                    onClick={(e) => deleteChat(session.id, e)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="p-3 md:p-4 border-b flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h2 className="font-semibold text-sm md:text-base">AI Shopping Assistant</h2>
              {/* Mobile: New Chat Button */}
              <Button 
                size="icon" 
                variant="ghost" 
                onClick={createNewChat}
                className="md:hidden h-8 w-8"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <Button size="icon" variant="ghost" onClick={onClose} className="h-8 w-8 md:h-10 md:w-10">
              <X className="h-4 w-4 md:h-5 md:w-5" />
            </Button>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-3 md:p-4">
            <div className="space-y-3 md:space-y-4">
              {currentSession?.messages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] md:max-w-[80%] p-2.5 md:p-3 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    <p className="text-xs md:text-sm break-words">{msg.content}</p>
                    <p className="text-[10px] md:text-xs mt-1 opacity-70">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-muted p-2.5 md:p-3 rounded-lg">
                    <p className="text-xs md:text-sm">Agent is typing...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-3 md:p-4 border-t">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                sendMessage();
              }}
              className="flex space-x-2"
            >
              <Input
                placeholder="Type your message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={isTyping}
                className="text-sm md:text-base"
              />
              <Button type="submit" disabled={isTyping || !message.trim()} size="icon" className="flex-shrink-0">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>
      </Card>
    </div>
  );
}