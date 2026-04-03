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

  return res.json();
};

export const getSessions = async () => {
  const res = await fetch(`${BASE_URL}/sales/sessions`, {
    headers: getAuthHeaders()
  });

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
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
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