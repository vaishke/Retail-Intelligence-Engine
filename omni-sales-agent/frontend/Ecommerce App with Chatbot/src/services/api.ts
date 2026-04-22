const BASE_URL = "http://localhost:8000"; // your FastAPI

const getAuthHeaders = () => ({
  "Content-Type": "application/json",
  "Authorization": `Bearer ${localStorage.getItem("token")}`
});

export const startSession = async () => {
  const res = await fetch(`${BASE_URL}/sales/session/start`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ channel: "web" })
  });

  if (!res.ok) throw new Error("Failed to start session");
  return res.json();
};

export const sendChatToBackend = async (message: string, session_id: string) => {
  const res = await fetch(`${BASE_URL}/sales/chat`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      session_id,
      message,
      channel: "web"
    })
  });

  if (!res.ok) throw new Error("Failed to send chat message");
  return res.json();
};

export const getSessions = async () => {
  const res = await fetch(`${BASE_URL}/sales/sessions`, {
    headers: getAuthHeaders()
  });

  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
};

export const getSessionById = async (sessionId: string) => {
  const res = await fetch(`${BASE_URL}/sales/session/${sessionId}`, {
    headers: getAuthHeaders()
  });

  if (!res.ok) throw new Error("Failed to fetch session");
  return res.json();
};

export const deleteSession = async (sessionId: string) => {
  const res = await fetch(`${BASE_URL}/sales/session/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders()
  });

  if (!res.ok) throw new Error("Failed to delete session");
  return res.json();
};

export async function fetchProducts() {
  const res = await fetch(`${BASE_URL}/products`);
  return res.json();
}

export async function fetchCart(userId: string) {
  const res = await fetch(`${BASE_URL}/cart/${userId}`);
  return res.json();
}

export async function addToCart(userId: string, productId: string, quantity: number) {
  const res = await fetch(`${BASE_URL}/cart/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, product_id: productId, quantity }),
  });
  return res.json();
}

export async function placeOrder(payload: any) {
  const res = await fetch(`${BASE_URL}/orders`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.detail?.message || data?.message || "Failed to place order");
  }

  return data;
}

export async function fetchOrders() {
  const res = await fetch(`${BASE_URL}/orders`, {
    headers: getAuthHeaders(),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.detail || data?.message || "Failed to fetch orders");
  }

  return data.orders || [];
}

// export async function sendChatToBackend(message: string, userId: string) {
//   const res = await fetch("http://localhost:8000/sales/chat", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ user_id: userId, message }),
//   });

//   if (!res.ok) throw new Error("Failed to fetch");

//   const data = await res.json();
//   return data; // make sure this is JSON parsed
// }
