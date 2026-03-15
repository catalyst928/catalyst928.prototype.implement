const ORDER_URL = 'http://localhost:8001/order/create'

export interface OrderResponse {
  order?: {
    order_id: string
    state: string
    order_date: string
  }
  notification?: {
    message_id: string
    status: 'sent' | 'failed'
    sent_at: string
  }
  error?: {
    code: number
    message: string
    step: string
  }
}

export async function placeOrder(customerId: string, offerId: string): Promise<OrderResponse> {
  const resp = await fetch(ORDER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId, offer_id: offerId }),
  })
  return resp.json() as Promise<OrderResponse>
}
