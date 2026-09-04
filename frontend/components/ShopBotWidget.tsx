"use client";

import { useState, useEffect, useRef } from "react";
import { Bot, User, Send, X, ShoppingCart, AlertCircle, Shield, CheckCircle } from "lucide-react";
import api from "@/lib/api";
import { AP2Crypto } from "@/lib/ap2";
import { formatCurrency } from "@/lib/utils";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  data?: any;
}

interface ShopBotWidgetProps {
  merchantId?: string;
  buyerDid?: string;
  initialMessage?: string;
  autoOpen?: boolean;
}

export default function ShopBotWidget({
  merchantId = "m_test",
  buyerDid = "did:example:buyer_demo",
  initialMessage,
  autoOpen = false,
}: ShopBotWidgetProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [buyerKey, setBuyerKey] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate buyer key once (persisted in localStorage for session continuity)
  useEffect(() => {
    let key = localStorage.getItem("store_buyer_key");
    if (!key) {
      key = AP2Crypto.generatePrivateKey();
      localStorage.setItem("store_buyer_key", key);
    }
    setBuyerKey(key);

    // If initialMessage prop is provided, show it as a system message
    if (initialMessage) {
      setMessages([
        {
          role: "system",
          content: initialMessage,
          timestamp: new Date(),
        },
      ]);
    }
  }, [initialMessage]);

  // Auto-open if triggered
  useEffect(() => {
    if (autoOpen) {
      setOpen(true);
    }
  }, [autoOpen]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/api/v1/demo/shopbot", {
        merchant_id: merchantId,
        buyer_did: buyerDid,
        message: input,
        buyer_private_key: buyerKey,
      });

      const data = res.data;
      let reply: Message;

      if (data.status === "success") {
        reply = {
          role: "assistant",
          content: data.message || "✅ Purchase completed!",
          timestamp: new Date(),
          data,
        };
      } else if (data.status === "denied") {
        reply = {
          role: "assistant",
          content: `❌ ${data.message}`,
          timestamp: new Date(),
          data,
        };
      } else if (data.status === "no_products") {
        reply = {
          role: "assistant",
          content: "I couldn't find any products matching your request.",
          timestamp: new Date(),
          data,
        };
      } else {
        reply = {
          role: "assistant",
          content: data.message || "ShopBot: How can I help you?",
          timestamp: new Date(),
          data,
        };
      }

      setMessages((prev) => [...prev, reply]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.response?.data?.detail || err.message}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating trigger button */}
      !open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="shopbot-float-button fixed bottom-6 right-6 z-50 flex items-center justify-center w-14 h-14 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors"
          aria-label="ShopBot"
        >
          <ShoppingCart className="w-6 h-6" />
        </button>
      )

      {/* Chat dialog */}
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          className="shopbot-dialog fixed inset-0 z-50 flex items-end justify-end p-4 bg-black/50"
        >
          <div className="shopbot-panel w-80 h-96 bg-card border border-border rounded-2xl shadow-xl flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-border bg-muted/50">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-primary" />
                <span className="font-medium">ShopBot</span>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="shopbot-close-btn p-1 rounded-lg hover:bg-muted transition-colors"
                aria-label="Close ShopBot"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Messages */}
            <div className="shopbot-messages flex-1 overflow-y-auto p-3 space-y-3">
              {messages.map((msg, i) => {
                const isBot = msg.role === "assistant" || msg.role === "system";
                return (
                  <div key={i}>
                    {msg.role === "system" ? (
                      <div className="bg-muted rounded-lg p-2 text-sm text-muted-foreground">
                        {msg.content}
                      </div>
                    ) : (
                      <div
                        className={`rounded-lg p-2 text-sm ${
                          msg.role === "user"
                            ? "bg-primary text-primary-foreground ml-auto max-w-[80%]"
                            : "bg-muted mr-auto max-w-[80%]"
                        }`}
                      >
                        <div className="flex items-start gap-1.5">
                          {isBot && <Bot className="w-3 h-3 mt-0.5 flex-shrink-0" />}
                          <div className="whitespace-pre-wrap flex-1">{msg.content}</div>
                          {msg.role === "user" && (
                            <User className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          )}
                        </div>

                        {/* Product details */}
                        {msg.data?.product && (
                          <div className="mt-1.5 p-1.5 bg-background/10 rounded border text-xs">
                            <div className="font-medium">
                              Product: {msg.data.product.name}
                            </div>
                            <div className="text-muted-foreground">
                              Price: {formatCurrency(msg.data.product.base_price_paise)}
                            </div>
                          </div>
                        )}

                        {/* Razorpay order */}
                        {msg.data?.razorpay_order && (
                          <div className="mt-1.5 p-1.5 bg-green-100 dark:bg-green-900/30 rounded border border-green-200 text-xs">
                            <CheckCircle className="w-3 h-4 inline mr-1 text-green-600" />
                            Order: {msg.data.razorpay_order.id}
                          </div>
                        )}

                        {/* Guardian decision */}
                        {msg.data?.guardian_decision && (
                          <div className="mt-1.5 p-1.5 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 text-xs">
                            <Shield className="w-3 h-4 inline mr-1 text-amber-600" />
                            Guardian: {msg.data.guardian_decision.decision}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
              {loading && (
                <div className="bg-muted mr-auto max-w-[80%] rounded-lg p-2 text-sm">
                  <Bot className="w-3 h-3 inline mr-1" />
                  Thinking...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-2 border-t border-border">
              <div className="flex gap-1.5">
                <input
                  type="text"
                  placeholder="Type your request..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
                  disabled={loading}
                  className="flex-1 px-2 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary bg-background"
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim() || !buyerKey}
                  className="px-2 py-1.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Merchant: {merchantId} | Buyer: {buyerDid}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
