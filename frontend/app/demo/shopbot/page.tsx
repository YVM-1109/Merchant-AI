"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useState, useEffect, useRef } from "react";
import { Send, Bot, User, ShoppingCart, CheckCircle, AlertCircle, Shield } from "lucide-react";
import { AP2Crypto } from "@/lib/ap2";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  data?: any;
}

interface Product {
  product_id: string;
  name: string;
  base_price_paise: number;
  category: string;
}

export default function ShopBotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content: "🤖 ShopBot ready! I can help you buy products. Try 'I want to buy a wireless mouse for under ₹1000'.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [buyerKey, setBuyerKey] = useState("");
  const [merchantId] = useState("m_test");
  const [buyerDid] = useState("did:example:buyer_demo");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate buyer private key on mount
  useEffect(() => {
    const key = AP2Crypto.generatePrivateKey();
    setBuyerKey(key);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function sendMessage() {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
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
      let botReply: Message;

      if (data.status === "success") {
        botReply = {
          role: "assistant",
          content: data.message || "Purchase completed successfully!",
          timestamp: new Date(),
          data,
        };
      } else if (data.status === "no_products") {
        botReply = {
          role: "assistant",
          content: "I couldn't find any products matching your request.",
          timestamp: new Date(),
          data,
        };
      } else if (data.status === "denied") {
        botReply = {
          role: "assistant",
          content: `❌ ${data.message}`,
          timestamp: new Date(),
          data,
        };
      } else {
        botReply = {
          role: "assistant",
          content: data.message || "ShopBot: I need more details about what you're looking for.",
          timestamp: new Date(),
          data,
        };
      }

      setMessages((prev) => [...prev, botReply]);
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
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "system" ? (
              <div className="bg-muted rounded-lg p-3 text-sm">
                {msg.content}
              </div>
            ) : (
              <div
                className={`rounded-lg p-3 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground ml-auto max-w-[80%]"
                    : "bg-card border mr-auto max-w-[80%]"
                }`}
              >
                <div className="flex items-start gap-2">
                  {msg.role === "assistant" && (
                    <Bot className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                  {msg.role === "user" && (
                    <User className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  )}
                </div>

                {/* Show product/order details */}
                {msg.data?.product && (
                  <div className="mt-2 p-2 bg-background/10 dark:bg-background/20 rounded border text-xs">
                    <div className="font-medium">
                      Product: {msg.data.product.name}
                    </div>
                    <div className="text-muted-foreground">
                      Price: {formatCurrency(msg.data.product.base_price_paise)}
                    </div>
                  </div>
                )}

                {msg.data?.razorpay_order && (
                  <div className="mt-2 p-2 bg-green-100 dark:bg-green-900/30 rounded border border-green-200 text-xs">
                    <CheckCircle className="w-3 h-4 inline mr-1 text-green-600" />
                    Order: {msg.data.razorpay_order.id}
                  </div>
                )}

                {msg.data?.guardian_decision && (
                  <div className="mt-2 p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 text-xs">
                    <Shield className="w-3 h-4 inline mr-1 text-amber-600" />
                    Guardian: {msg.data.guardian_decision.decision}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-3 bg-card">
        <div className="text-xs text-muted-foreground mb-1">
          Merchant: {merchantId} | Buyer: {buyerDid}
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Type your request..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
            disabled={loading}
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
