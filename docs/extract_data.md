# 🛠️ Project Setup Guide

This document provides **step-by-step instructions** to set up the development environment and explains the purpose of each step involved in running the project.

---

## 🧪 Virtual Environment Setup

A **Python virtual environment (venv)** allows you to create an isolated Python environment specific to this project, separate from the system-wide Python installation.

### Why Use a Virtual Environment?

Using a virtual environment helps to:

- Maintain a **project-specific Python version and dependencies**
- Avoid conflicts between multiple Python projects
- Prevent issues caused by installing or upgrading incompatible Python versions
- Work with different Python versions independently across projects

All required libraries for this project will be installed **inside the virtual environment**, ensuring a consistent and reproducible setup.

---

### 📌 Prerequisites

Ensure Python 3 is installed on your system:
```bash
python --version
```

### 🔧 Create a Virtual Environment
- Navigate to the project root directory and run the below command to run in the powershell to create the virtual environment
```powershell
python3 -m venv venv
```
### 📌 Why `py -3 -m venv venv`?

- Ensures **Python 3** is used explicitly on Windows systems
- Avoids conflicts when multiple Python versions are installed
- Recommended by Python documentation for Windows environments

### ✅ Activate the Virtual Environment

Run the following command in **PowerShell** to activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

#### Activating the virtual environment:

- Switches the terminal to use the project-specific **Python interpreter**
- Ensures all installed dependencies are resolved from the local environment
- Prevents conflicts with system-wide Python packages

---
## 🕸️ Web Scraping (YouTube Data API)

We use the **`requests`** library in Python to connect to the **YouTube Data API** and retrieve data for a specific YouTube channel.  
Follow the steps below to extract the required data from a channel using its **channel handle**.

---

### Step 1: Retrieve the Playlist ID of a YouTube Channel

To fetch videos from a YouTube channel, we first need the **playlist ID** of the channel’s *uploads playlist*.  
This playlist contains all the videos uploaded by the channel.

Given a **channel handle**, we can retrieve the playlist ID using the following API endpoint:
https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}

### Connect to the API and Fetch the Response

Use the following Python code to send a request to the YouTube Data API and read the response:

```python
url = (f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}")
response = requests.get(url)
data = response.json()
print(data)
```

### API Response Structure

The response is returned in JSON format, similar to the structure shown below:

<img width="1843" height="537" alt="YouTube API response structure" src="https://github.com/user-attachments/assets/b59f4318-7127-4202-a270-e5db6b09f38f" />

## Extract the Playlist ID

From the response, the uploads playlist ID can be extracted using the following key path:

```python
playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
```
This `playlist_id` will be used in subsequent steps to fetch video-level data for the channel.

Collectively, we can define a function `get_playlist_id()` which will fetch the playlist_id as shown below:

```python
def get_playlist_id():
    try:
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANNEL_HANDLE}&key={API_KEY}"

        response = requests.get(url)

        response.raise_for_status()

        data = response.json()
    
        channel_playlistId = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        return channel_playlistId
    
    except requests.exceptions.RequestException as e:
        raise e
```

---

### Step 2: Retrieve Video IDs from the Playlist ID

In this step, we fetch the **video IDs** from the **playlist ID** obtained in **Step 1**.  
Each YouTube channel’s uploads playlist contains all the videos uploaded by that channel.

Given a **playlist id**, we can retrieve the video id's using the following API endpoint:
https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}

### Connect to the API and Fetch the Response

Use the following Python code to send a request to the YouTube Data API and read the response:

```python
url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}"
response = requests.get(url)
data = response.json()
print(data)
```
### API Response Structure

The response is returned in JSON format, similar to the structure shown below:

<img width="1858" height="697" alt="YouTube playlistItems API response" src="https://github.com/user-attachments/assets/349efce2-9d3e-4214-94e5-710c29fdd1ed" />

### From the response:
- data["pageInfo"] contains resultsPerPage and totalResults
- The maximum value for resultsPerPage is 50

Because of this limit, we must paginate through the results to retrieve all video IDs.
Pagination is handled using the nextPageToken field:

- If nextPageToken is present, another request must be made
- Pagination continues until nextPageToken is None

### Pagination Logic
For each page:
- Iterate through data["items"]
- Extract the videoId from item["contentDetails"]["videoId"]
- Append each videoId to a list
- Move to the next page using nextPageToken

Collectively, we can define a function `get_video_ids()` which will fetch the video_id's from the playlist as shown below:
```python
def get_video_ids(playlistId):
    video_ids = []
    pageToken = None
    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}"

    try:
        while True:
            url = base_url
            if pageToken:
                url += f"&pageToken={pageToken}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data.get('items',[]):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            pageToken = data.get('nextPageToken')
            if not pageToken:
                break
        return video_ids
    except requests.exceptions.RequestException as e:
        raise e
```
The function returns a list of video IDs, which can be used in subsequent steps to fetch video-level statistics.

---
### Step 3: Retrieve Video Statistics Using Video IDs

In this step, we fetch **video-level statistics** for each **video ID** obtained in **Step 2**.

Given one or more **video IDs**, video statistics can be retrieved using the following API endpoint:  

Given a **video id**, we can retrieve the video stats using the following API endpoint:
https://youtube.googleapis.com/youtube/v3/videos?part=statistics&part=snippet&part=contentDetails&id={video_ids_str}&key={API_KEY}

### API Response Structure

The response is returned in JSON format, similar to the structure shown below:

<img width="1920" height="965" alt="image" src="https://github.com/user-attachments/assets/19ff1b07-071e-481d-bf88-e8e2e8eea435" />

### Breaking Down the API Logic

- The `id` parameter accepts **multiple video IDs as a comma-separated string** (`video_ids_str`).
- The API has a **maximum limit of 50 video IDs per request**.
- To handle this limit, the list of video IDs obtained in Step 2 is split into **batches** (each containing up to 50 IDs).
- Each batch is converted into a comma-separated string and passed to the API iteratively.
- From the API response, we extract:
  - **Title** and **Published Date** from `snippet`
  - **Duration** from `contentDetails`
  - **View Count**, **Like Count**, and **Comment Count** from `statistics`

### Function to Extract Video Statistics

The following function retrieves video statistics for all video IDs by handling batching internally:
```python
def extract_video_data(video_ids):
    extracted_data = []

    def batch_list(video_id_lst, batch_size):
        for video_id in range(0,len(video_id_lst),batch_size):
            yield video_id_lst[video_id : video_id + batch_size]

    try:
        for batch in batch_list(video_ids, 3):
            video_ids_str = ",".join(batch)
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=statistics&part=snippet&part=contentDetails&id={video_ids_str}&key={API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data.get('items',[]):
                video_id = item['id']
                snippet = item['snippet']
                contentDetails = item['contentDetails']
                statistics = item['statistics']
            
                video_data = {
                    "video_id": video_id,
                    "title": snippet['title'],
                    "publishedAt": snippet['publishedAt'],
                    "duration": contentDetails['duration'],
                    "viewCount": statistics.get('viewCount',None),
                    "likeCount": statistics.get('likeCount',None),
                    "commentCount": statistics.get('commentCount',None), 
                }

                extracted_data.append(video_data)
        return extracted_data
    except requests.exceptions.RequestException as e:
        raise e
```

The above function returns a list of dictionaries that contains all the video stats for each video_id.

---
### Step 4: Save Video Statistics Data to a JSON File

In this step, the video statistics retrieved from the YouTube Data API are saved locally for **staging and downstream processing**.

The data is stored in the **JSON format** inside the `data/` directory.  
Each file name is suffixed with the **current date**, which acts as a **batch identifier** for daily processing.

The following function saves the extracted video statistics into a JSON file with the required naming convention:

```python
def save_to_json(extracted_data):
    file_path = f"./data/Youtube_data_{date.today()}.json"
    with open(file_path, "w", encoding="utf-8") as json_outfile:
        json.dump(extracted_data, json_outfile, indent=4, ensure_ascii=False)
```






