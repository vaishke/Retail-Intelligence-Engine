from langgraph.graph import StateGraph, END
from sales_graph.state import SalesState

from sales_graph.nodes.recommend import recommendation_node
from sales_graph.nodes.inventory import inventory_node
from sales_graph.nodes.cart import cart_node
from sales_graph.nodes.offers import offers_node
from sales_graph.nodes.payment import payment_node
from sales_graph.nodes.fulfillment import fulfillment_node
from sales_graph.nodes.post_purchase import post_purchase_node


def build_sales_graph():
    graph = StateGraph(SalesState)

    graph.add_node("recommend", recommendation_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("cart", cart_node)
    graph.add_node("offers", offers_node)
    graph.add_node("payment", payment_node)
    graph.add_node("fulfillment", fulfillment_node)
    graph.add_node("post_purchase", post_purchase_node)

    graph.set_entry_point("recommend")

    graph.add_edge("recommend", "inventory")
    graph.add_edge("inventory", "cart")
    graph.add_edge("cart", "offers")
    graph.add_edge("offers", "payment")
    graph.add_edge("payment", "fulfillment")
    graph.add_edge("fulfillment", "post_purchase")
    graph.add_edge("post_purchase", END)

    return graph.compile()
