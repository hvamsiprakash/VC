import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to get video comments
def get_video_comments(video_id):
    try:
        comments = []
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        while "items" in results:
            for item in results["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            # Get the next set of results
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    pageToken=results["nextPageToken"],
                    maxResults=100
                ).execute()
            else:
                break

        return comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching comments: {e}")
        return []

# Function to analyze and categorize comments sentiment
def analyze_and_categorize_comments(comments):
    try:
        categorized_comments = {'Positive': [], 'Neutral': [], 'Negative': []}
        comment_analysis = []

        for comment in comments:
            analysis = TextBlob(comment)
            polarity = analysis.sentiment.polarity
            subjectivity = analysis.sentiment.subjectivity
            comment_analysis.append({"Comment": comment, "Polarity": polarity, "Subjectivity": subjectivity})

            # Classify the polarity of the comment
            if polarity > 0:
                categorized_comments['Positive'].append((comment, polarity, subjectivity))
            elif polarity == 0:
                categorized_comments['Neutral'].append((comment, polarity, subjectivity))
            else:
                categorized_comments['Negative'].append((comment, polarity, subjectivity))

        comments_df = pd.DataFrame(comment_analysis)
        return categorized_comments, comments_df
    except Exception as e:
        st.error(f"Error analyzing comments: {e}")
        return {'Positive': [], 'Neutral': [], 'Negative': []}, pd.DataFrame()

# Main Streamlit app
st.title("YouTube Comments Sentimental Analysis")

st.markdown(
    """
    🎬 Analyze the sentiment of YouTube video comments with insightful visualizations! 
    Enter a YouTube Video ID below, and we will fetch the comments, analyze them, 
    and provide detailed charts to explore the sentiment trends.
    """
)

video_id = st.text_input("Enter YouTube Video ID", value="")

if st.button("Analyze Comments"):
    comments = get_video_comments(video_id)
    
    if comments:
        categorized_comments, comments_df = analyze_and_categorize_comments(comments)

        # Display Sentiment Summary
        st.subheader("Sentiment Summary")
        st.write(f"**Total Positive Comments:** {len(categorized_comments['Positive'])}")
        st.write(f"**Total Neutral Comments:** {len(categorized_comments['Neutral'])}")
        st.write(f"**Total Negative Comments:** {len(categorized_comments['Negative'])}")

        # Chart 1: Sentiment Distribution Bar Chart
        sentiment_counts = {
            "Positive": len(categorized_comments['Positive']),
            "Neutral": len(categorized_comments['Neutral']),
            "Negative": len(categorized_comments['Negative'])
        }
        fig_sentiment_bar = px.bar(
            x=list(sentiment_counts.keys()), 
            y=list(sentiment_counts.values()), 
            color=list(sentiment_counts.keys()), 
            title="Sentiment Distribution",
            labels={"x": "Sentiment", "y": "Count"}
        )
        st.plotly_chart(fig_sentiment_bar)

        # Chart 2: Polarity and Subjectivity Distribution
        fig_polarity_subjectivity = px.scatter(
            comments_df, x="Polarity", y="Subjectivity", 
            color=comments_df["Polarity"].apply(lambda x: "Positive" if x > 0 else "Negative" if x < 0 else "Neutral"),
            title="Polarity vs Subjectivity",
            labels={"Polarity": "Polarity", "Subjectivity": "Subjectivity"},
            hover_data=["Comment"]
        )
        st.plotly_chart(fig_polarity_subjectivity)

        # Chart 3: Polarity Over Time (Assuming sorted by comment order)
        comments_df['Comment Index'] = comments_df.index + 1
        fig_polarity_time = px.line(
            comments_df, x='Comment Index', y='Polarity', 
            title="Polarity Over Time (Comment Index)",
            labels={"Comment Index": "Comment Number", "Polarity": "Polarity"},
            hover_data=["Comment"]
        )
        st.plotly_chart(fig_polarity_time)

        # Show filtered comments
        st.subheader("Filtered Comments by Sentiment")
        selected_sentiment = st.selectbox("Select Sentiment", ["Positive", "Neutral", "Negative"])
        
        filtered_comments = categorized_comments[selected_sentiment]
        st.write(f"Displaying {len(filtered_comments)} {selected_sentiment} comments:")
        
        for idx, comment_info in enumerate(filtered_comments[:20]):
            comment_text, polarity, subjectivity = comment_info
            st.write(f"{idx + 1}. {comment_text} (Polarity: {polarity}, Subjectivity: {subjectivity})")

