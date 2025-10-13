from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import aiofiles
import aiohttp
import asyncio

# Define transport with GraphQL API URL, get access token from account created
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0eXBlIjoiSW50ZWdyYXRpb25BY2Nlc3NUb2tlbiIsInZlcnNpb24iOiIxLjAiLCJpbnRlZ3JhdGlvbklkIjoxOTMzLCJ1c2VySWQiOjI2ODI0NywiYWNjZXNzVG9rZW5TZWNyZXQiOiI4NTI0OWMxMmI1Y2EzNTNmODk3ZmRiYjFkMDdmMjI0ZGUxZjg3OTkzNDY0YTk3NWE5NTdmYjhmYWRlMjEyMmQ1IiwiaWF0IjoxNzYwMDg0ODE4fQ.TfLH8RA0mf5JI7yAovHQ4F0L1TcdoGmENj4rR8g2muY"
transport = RequestsHTTPTransport(
    url='https://api.cyanite.ai/graphql', # HTTP endpoint
    headers={"Authorization": f"Bearer {access_token}"},
    verify=True,
    retries=3,
)
client = Client(transport=transport, fetch_schema_from_transport=False)

def get_tracks_test():
    '''
    Define get_tracks Query
    This will fetch the first 10 library tracks with their audio analysis type names.
    You can run this for quick verification on whether it fetches data
    returns a dictionary with the query results
    '''
    query = gql("""
                query {
                    libraryTracks(first: 10) {
                pageInfo {
                  hasNextPage
                }
                edges {
                  node {
                    audioAnalysisV7 {
                      __typename
                    }
                  }
                }
              }
            }
              """)
    # Execute the query and return the result
    return client.execute(query)

def get_tracks_info_query():
    '''
    Define libraryTracks Query for title, id and audio analysis type names
    This will fetch the first 5 library tracks with their title, id, genre tags, mood tags, emotional profile and emotional dynamics.
    returns a dictionary with the query results
    '''
    variables = {
        "first": 5,
        "after": None
        }
    query = gql("""
                query PaginatedLibraryTracksQuery($first: Int!, $after: String) {
              libraryTracks(
                # amount of items that should be fetched (for free account its 5 only, maximum/default is 50)
                first: $first
                # cursor after which items should be fetched
                after: $after
              ){
                pageInfo {
                  hasNextPage
                }
                edges {
                  cursor
                  node {
                    id
                    title
                    # We can specify what kind of data we want to select by adding them to our selection set.
                    audioAnalysisV7 {
                      __typename
                      ... on AudioAnalysisV7Finished {
                        result {
                          genreTags
                          moodTags
                          emotionalProfile
                          emotionalDynamics
                        }
                      }
                    }
                  }
                }
              }
            }
                
                """)
    return client.execute(query,variable_values=variables)
def GrabCyanitelink():
    '''
    Obtain the URL and ID from Cyanite to upload the song in to
    Returns the URL and ID for uploading only
    '''
    mutate = gql("""
                      mutation FileUploadRequestMutation {
        fileUploadRequest {
          # id will be used for creating the library track from the file upload
          id
          # uploadUrl specifies where we need to upload the file to
          uploadUrl
        }
      }
                      """)
    dictlist=client.execute(mutate)
    url=dictlist.get('fileUploadRequest').get('uploadUrl')
    uploadedID=dictlist.get('fileUploadRequest').get('id')
    return (url,uploadedID)

def uploadtracktoCyaniteAndAnalyse(link):
    '''
    Uploads MP3 file to the Cyanite database and inititate analysis
    Location for MP3 file is placed at the project folder
    returns the Cyanite Library ID for data
    '''
    print ("Running upload and analyse")
    print ("Uploading")
    upload_url = link[0]
    file_name = "[SlipySlidy] [MapleStory BGM] Arcana∩╝Ü The Tune of the Azure Light -gleam-.mp3"
    variables1 = {
    "input": { "uploadId": link[1], "title": file_name } 
    }

    async def main():
      async with aiofiles.open(file_name, 'rb') as f:
          body = await f.read()
      async with aiohttp.ClientSession() as session:
          headers = {"Content-Type": "audio/mpeg"}
          async with session.put(upload_url, data=body, headers=headers) as resp:
              result = await resp.text()
              print(result)

    if __name__ == "__main__":
        asyncio.run(main())
    print ("Upload Done")
    print ("Creating Library Track")
    mutate = gql("""
                mutation LibraryTrackCreateMutation($input: LibraryTrackCreateInput!) {
                  libraryTrackCreate(input: $input) {
                    __typename
                    ... on LibraryTrackCreateSuccess {
                      createdLibraryTrack {
                        id
                      }
                    }
                    ... on LibraryTrackCreateError {
                      code
                      message
                    }
                  }
                }
                """)
    dictlist=client.execute(mutate,variable_values=variables1)
    print ("Library Track Created")
    libraryID=dictlist.get('libraryTrackCreate').get('createdLibraryTrack').get('id')

    variables2={
    "input": { "libraryTrackId": libraryID }
    }
    print ("Analysing")
    mutate2 = gql("""
                  mutation LibraryTrackEnqueueMutation($input: LibraryTrackEnqueueInput!) {
                  libraryTrackEnqueue(input: $input) {
                    __typename
                    ... on LibraryTrackEnqueueSuccess {
                      enqueuedLibraryTrack {
                        id
                        audioAnalysisV7 {
                          # if enqueued typename should be AudioAnalysisV7Enqueued
                          __typename
                        }
                      }
                    }
                    ... on LibraryTrackEnqueueError {
                      code
                      message
                    }
                  }
                }
                """)
    
    client.execute(mutate2,variable_values=variables2)
    return(libraryID)


def get_all_tracks_info():
    '''
    Obtains every information required from the Cyanite database
    Returns a dictionary of information from Cyanite, not cleaned
    '''
    PDictInfo=get_tracks_info_query()
    return PDictInfo

def store_info(PDictInfo):
  '''
  Filters out the unnecessary information in the nodes and stores the relevant details in a structured format.
  Each dictionary is characterised by their respective library IDs
  Returns a list of cleaned up data to decipher, below is the respective index and datas
  index 0 is Title
  index 1 is Genre Tags
  index 2 is Mood Tags
  index 3 is Emotional Profile
  index 4 is Emotional Dynamics
  '''
  StoredListInfo=[]
  ListofTracks=PDictInfo.get('libraryTracks').get('edges')
  for track in ListofTracks:
      node=track.get('node')
      title=node.get('title')
      id=node.get('id')
      audio_analysis=node.get('audioAnalysisV7')
      if audio_analysis.get('__typename')=='AudioAnalysisV7Finished':
          result=audio_analysis.get('result')
          genre_tags=result.get('genreTags')
          mood_tags=result.get('moodTags')
          emotional_profile=result.get('emotionalProfile')
          emotional_dynamics=result.get('emotionalDynamics')
          DictEntryStore={f"{id}":({"Title":f"{title}"},{"Genre Tags":f"{genre_tags}"},{"Mood Tags":f"{mood_tags}"}, {"Emotional Profile":f"{emotional_profile}"},{"Emotional Dynamics":f"{emotional_dynamics}"})}
          StoredListInfo.append(DictEntryStore)
  return StoredListInfo        

def get_titlefromID(StoreListinfo, ID):
    '''
    Obtains the title based on the given ID
    Returns a single item list of the title
    '''
    for info in StoreListinfo:
        try:
            title=info.get(ID)[0].get('Title')
        except:
            pass
    return title

def get_genretagsfromID(StoreListinfo, ID):
    '''
    Obtains the genre tags based on the given ID
    Returns a list of genres
    '''
    for info in StoreListinfo:
        try:
            genretags=info.get(ID)[1].get('Genre Tags')
        except:
            pass
    return genretags

def get_moodtagsfromID(StoreListinfo, ID):
    '''
    Obtains the mood tags based on the given ID
    Returns a list of moods
    '''
    for info in StoreListinfo:
        try:
            moodtags=info.get(ID)[2].get('Mood Tags')
        except:
            pass
    return moodtags
def get_emotionalprofilefromID(StoreListinfo, ID):
    '''
    Obtains the mood tags based on the given ID
    Returns a list of moods
    '''
    for info in StoreListinfo:
        try:
            emotionalprofile=info.get(ID)[3].get('Emotional Profile')
        except:
            pass
    return emotionalprofile
def get_emotionaldynamicsfromID(StoreListinfo, ID):
    '''
    Obtains the mood tags based on the given ID
    Returns a list of emotional dynamics
    '''
    for info in StoreListinfo:
        try:
            emotionaldynamics=info.get(ID)[4].get('Emotional Dynamics')
        except:
            pass
    return emotionaldynamics

def PreviousUploaddedID(StoredInfo):
    '''
    Obtains the libraryID of the most recent upload
    Returns the LibraryID string
    '''
    ID=list(StoredInfo[0].keys())[0]
    return (ID)

def IndexID(StoredInfo,index):
    '''
    Obtains the libraryID based on the given index
    Indexing is based on the upload order
    only from 0-5, 0 will return the 1st song by default
    if given index >5, error will occur
    Returns the LibraryID string
    '''
    index=int(index)-1
    try:
      ID=list(StoredInfo[index].keys())[0]
    except:
      print ("Error, index out of range")
    return (ID)


def UploadingAndAnalysingMP3():
  """
  Execute the function for uploading and analysing the song
  It will constantly check whether the analysis is completed before moving to the next step
  """
  LinkAndID=GrabCyanitelink()
  LibraryAPIID=uploadtracktoCyaniteAndAnalyse(LinkAndID)
  listofstoredids=[]

  while not listofstoredids or LibraryAPIID not in listofstoredids:
      pdict_info = get_all_tracks_info()
      list_of_tracks = pdict_info.get('libraryTracks', {}).get('edges', [])
      #if not list_of_tracks:
          #break
      stored_info = store_info(pdict_info)
      listofstoredids = [next(iter(info)) for info in stored_info if info]

  print ("Analysis Completed")
  return ()



#UploadingAndAnalysingMP3()
PDictInfo=get_all_tracks_info()
#ListofTracks=PDictInfo.get('libraryTracks').get('edges')
#NameAndID=ListofTracks[0].get('node').get('id')
#LibraryID=NameAndID
StoredInfo=store_info(PDictInfo)
if StoredInfo==[]:
  print ("No finished analysis yet")
else:
  print (StoredInfo)

IDforLookup=IndexID(StoredInfo,1) #You can change the index here to get different IDs based on the order of upload
#IDforLookup=PreviousUploaddedID(StoredInfo) #You can use this function to get the most recently uploaded ID
title=get_titlefromID(StoredInfo, IDforLookup)
print (title)
'''
Left with verifying which conditions (mood, etc.) would allow/prevent the music from playing
If music is not suitable, regenerate another song without the 'negative' moods and revalidate again

'''
