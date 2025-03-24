# app.py

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import requests
from urllib.parse import urlparse, unquote
from datetime import datetime

# Helper function to extract Wikipedia page title from URL
def extract_title(url):
    try:
        path = urlparse(url).path
        title = path.split('/')[-1]
        return unquote(title)
    except Exception as e:
        return None

# Function to fetch daily pageviews using Wikimedia API with User-Agent header
def fetch_pageviews(title, start_date, end_date):
    base_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
    access = "all-access"
    agent = "user"
    project = "en.wikipedia.org"
    granularity = "daily"

    start = start_date.strftime('%Y%m%d')
    end = end_date.strftime('%Y%m%d')

    url = f"{base_url}/{project}/{access}/{agent}/{title}/{granularity}/{start}/{end}"

    headers = {
        'User-Agent': 'WikiTrendsApp/1.0 (mailto:your_email@example.com)'  # Replace with your email
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Error fetching data for {title}: {response.status_code}")

    data = response.json()
    views = {
        datetime.strptime(item['timestamp'], '%Y%m%d00'): item['views']
        for item in data['items']
    }

    df = pd.DataFrame(views.items(), columns=['Date', title])
    df.set_index('Date', inplace=True)
    return df

# Main function to run in Gradio
def compare_views(url1, url2, start_date_str, end_date_str):
    try:
        if not (url1 and url2 and start_date_str and end_date_str):
            return "Please enter all fields.", None

        title1 = extract_title(url1)
        title2 = extract_title(url2)

        if not (title1 and title2):
            return "Invalid Wikipedia URLs.", None

        start = pd.to_datetime(start_date_str)
        end = pd.to_datetime(end_date_str)

        df1 = fetch_pageviews(title1, start, end)
        df2 = fetch_pageviews(title2, start, end)

        merged_df = pd.merge(df1, df2, left_index=True, right_index=True, how='outer').fillna(0)

        plt.figure(figsize=(12, 6))
        plt.plot(merged_df.index, merged_df[title1], label=title1, linewidth=2)
        plt.plot(merged_df.index, merged_df[title2], label=title2, linewidth=2)
        plt.xlabel("Date")
        plt.ylabel("Daily Page Views")
        plt.title(f"Wikipedia Interest: {title1} vs {title2}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig("output_plot.png")
        plt.close()

        return merged_df.reset_index().to_html(index=False), "output_plot.png"

    except Exception as e:
        return f"Error: {str(e)}", None

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 📊 WikiTrends: Compare Wikipedia Page Interest Over Time")
    with gr.Row():
        url1 = gr.Textbox(label="Wikipedia URL 1", placeholder="e.g., https://en.wikipedia.org/wiki/Apple_Inc.")
        url2 = gr.Textbox(label="Wikipedia URL 2", placeholder="e.g., https://en.wikipedia.org/wiki/Samsung")
    with gr.Row():
        start = gr.Textbox(label="Start Date (YYYY-MM-DD)", placeholder="e.g., 2024-01-01")
        end = gr.Textbox(label="End Date (YYYY-MM-DD)", placeholder="e.g., 2024-03-01")
    submit = gr.Button("Compare Views")
    html_out = gr.HTML()
    plot_out = gr.Image()

    submit.click(fn=compare_views, inputs=[url1, url2, start, end], outputs=[html_out, plot_out])

# Launch the app
demo.launch()
