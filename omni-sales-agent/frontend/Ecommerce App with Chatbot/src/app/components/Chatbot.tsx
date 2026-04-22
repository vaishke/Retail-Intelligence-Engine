import { useState, useEffect, useRef } from 'react';
import { X, Send, Plus, Trash2, Bot, User } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Card } from './ui/card';
import { ChatSession, ChatMessage } from '../utils/mockData';
import { toast } from 'sonner';
import { deleteSession, getSessionById, getSessions, sendChatToBackend, startSession } from '../../services/api';

interface ChatbotProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Chatbot({ isOpen, onClose }: ChatbotProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const mapBackendMessage = (msg: any, index: number): ChatMessage => ({
    id: `${msg.timestamp || Date.now()}-${index}`,
    role: msg.role === 'assistant' ? 'agent' : 'user',
    content: msg.role === 'assistant'
      ? {
          message: msg.payload?.message || msg.message,
          products: msg.payload?.data?.recommendations || [],
          data: msg.payload?.data || {},
          prompt: msg.payload?.prompt || '',
        }
      : msg.message,
    timestamp: msg.timestamp || new Date().toISOString(),
  });

  const mapBackendSession = (session: any): ChatSession => ({
    id: session._id,
    title: session.title || 'New Chat',
    messages: Array.isArray(session.chat_history)
      ? session.chat_history.map(mapBackendMessage)
      : [],
    createdAt: session.metadata?.created_at || new Date().toISOString(),
  });

  useEffect(() => {
    if (!isOpen) return;

    const loadSessions = async () => {
      setIsLoadingSessions(true);
      try {
        const backendSessions = await getSessions();
        const formatted = backendSessions.map(mapBackendSession);
        setSessions(formatted);
        setCurrentSessionId((prev) => {
          if (prev && formatted.some((session) => session.id === prev)) {
            return prev;
          }
          return formatted[0]?.id ?? null;
        });
      } catch {
        toast.error('Failed to load chat history');
      } finally {
        setIsLoadingSessions(false);
      }
    };

    loadSessions();
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, currentSessionId]);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  const createNewChat = async () => {
    try {
      const newSession = await startSession();
      const formattedSession = mapBackendSession(newSession);
      setSessions((prev) => [formattedSession, ...prev]);
      setCurrentSessionId(newSession._id);
      toast.success('New chat created');
    } catch {
      toast.error('Failed to create new chat');
    }
  };

  const deleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      await deleteSession(id);
      setSessions((prev) => {
        const newSessions = prev.filter((s) => s.id !== id);
        if (currentSessionId === id) {
          setCurrentSessionId(newSessions[0]?.id ?? null);
        }
        return newSessions;
      });
      toast.success('Chat deleted');
    } catch {
      toast.error('Failed to delete chat');
    }
  };

  const sendMessage = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isTyping) return;

    let sessionId = currentSessionId;
    let sessionToUse = currentSession;

    if (!sessionId || !sessionToUse) {
      try {
        const newSession = await startSession();
        const formattedSession = mapBackendSession(newSession);
        setSessions((prev) => [formattedSession, ...prev]);
        setCurrentSessionId(newSession._id);
        sessionId = newSession._id;
        sessionToUse = formattedSession;
      } catch {
        toast.error('Failed to create chat');
        return;
      }
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: trimmedMessage,
      timestamp: new Date().toISOString(),
    };

    const updatedSession = {
      ...sessionToUse,
      title: sessionToUse.messages.length === 0 ? trimmedMessage.slice(0, 60) : sessionToUse.title,
      messages: [...sessionToUse.messages, userMessage],
    };

    setSessions((prev) => {
      const exists = prev.some((s) => s.id === sessionId);
      if (!exists) return [updatedSession, ...prev];
      return prev.map((s) => (s.id === sessionId ? updatedSession : s));
    });
    setMessage('');
    setIsTyping(true);

    try {
      const res = await sendChatToBackend(trimmedMessage, sessionId!);
      const agentMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: typeof res.response === 'string'
        ? { message: res.response, products: [], data: {} }
        : {
            message: res.response?.message || 'No response',
            products: res.response?.data?.recommendations || res.state?.recommended_items || [],
            data: res.response?.data || {},
            prompt: res.response?.prompt || '',
          },
        timestamp: new Date().toISOString(),
      };

      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, agentMessage],
      };

      setSessions((prev) => prev.map((s) => (s.id === sessionId ? finalSession : s)));

      // Refresh the active session from MongoDB so UI stays aligned with the DB source of truth.
      const persistedSession = await getSessionById(sessionId!);
      const mappedPersistedSession = mapBackendSession(persistedSession);
      setSessions((prev) => prev.map((s) => (s.id === sessionId ? mappedPersistedSession : s)));
      window.dispatchEvent(new Event("storage"));
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

      setSessions((prev) => prev.map((s) => (s.id === sessionId ? finalSession : s)));
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
              {!isLoadingSessions && sessions.length === 0 && (
                <p className="text-sm text-muted-foreground px-1">No chats yet</p>
              )}
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
              {!currentSession && !isLoadingSessions && (
                <p className="text-sm text-muted-foreground">
                  Start a new chat to talk with the AI shopping assistant.
                </p>
              )}
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

                        {(msg.content as any).data?.items?.length > 0 && (
                          <div className="rounded-lg border border-border/60 bg-background/70 p-3 space-y-2">
                            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                              Order Details
                            </p>
                            <div className="space-y-1">
                              {(msg.content as any).data.items.map((item: any, index: number) => (
                                <div
                                  key={`${item.product_id || item.name || 'item'}-${index}`}
                                  className="flex items-center justify-between gap-3 text-xs"
                                >
                                  <span className="font-medium">
                                    {item.name || item.product_name || 'Product'} x {item.qty || item.quantity || 1}
                                  </span>
                                  <span className="text-muted-foreground">
                                    Rs. {item.price ?? 0}
                                  </span>
                                </div>
                              ))}
                            </div>

                            {typeof (msg.content as any).data.cart_total !== 'undefined' && (
                              <div className="space-y-1 border-t pt-2 text-xs">
                                <div className="flex justify-between">
                                  <span>Cart total</span>
                                  <span>Rs. {(msg.content as any).data.cart_total}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Discount</span>
                                  <span>Rs. {(msg.content as any).data.discount || 0}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Points used</span>
                                  <span>{(msg.content as any).data.points_used || 0}</span>
                                </div>
                                <div className="flex justify-between font-semibold">
                                  <span>Final amount</span>
                                  <span>Rs. {(msg.content as any).data.final_amount || 0}</span>
                                </div>
                                <div className="flex justify-between text-muted-foreground">
                                  <span>Points earned</span>
                                  <span>{(msg.content as any).data.points_earned || 0}</span>
                                </div>
                                {(msg.content as any).data.new_tier && (
                                  <div className="flex justify-between text-muted-foreground">
                                    <span>Tier</span>
                                    <span>{(msg.content as any).data.new_tier}</span>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}

                        {(msg.content as any).data?.cart_items?.length > 0 && (
                          <div className="rounded-lg border border-border/60 bg-background/70 p-3 space-y-1">
                            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                              Cart
                            </p>
                            {(msg.content as any).data.cart_items.map((item: any, index: number) => (
                              <div
                                key={`${item.product_id || item.name || 'cart'}-${index}`}
                                className="flex items-center justify-between gap-3 text-xs"
                              >
                                <span>{item.name || 'Product'} x {item.qty || item.quantity || 1}</span>
                                <span className="text-muted-foreground">Rs. {item.price ?? 0}</span>
                              </div>
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
