# Affective Data Storytelling using LLM

This application is part of my Master's Dissertation project on generating data storytelling using large language models (LLMs). Although the term _data storytelling_ lacks a unified definition in the community, its primary goal is to communicate the insights from the dataset using visualisation and narratives to engage the user [1,2]. To make the narrative more engaging and resonate with the reader, emotional tone has been incorporated [3].

With the rise of LLMs and their capabilities in summarising and generating stories, this research explored how to utilise these capabilities and make generating data stories easier for both tech and non-tech. The user can input the CSV time-series dataset, file description and emotional tone to shape how the story is presented.

# Tech Stack

![Tech Stack for this Project](src/assets/tech-stack.png)

# Run the application

This repository contains the backend application.

To run the application locally:

1. Make sure you add the OpenAPI key in the .env file
2. Run the command

```
docker compose up
```

For the application to work, it must be run along with the frontend, which is located in this repository [LLM-APP](https://github.com/ikenichaa/llm-app)

# Application Demo

![Upload Page](src/assets/upload.png)
![Data storytelling](src/assets/agency.png)

# References

​​[1] E. Segel and J. Heer, “Narrative Visualization: Telling Stories with Data”.

​[2] H. Shao, R. Martinez-Maldonado, V. Echeverria, L. Yan, and D. Gasevic, “Data Storytelling in Data Visualisation: Does it Enhance the Efficiency and Effectiveness of Information Retrieval and Insights Comprehension?,” Conference on Human Factors in Computing Systems - Proceedings, vol. 1, May 2024, doi: 10.1145/3613904.3643022.

​[3] X. Lan, Y. Wu, and N. Cao, “Affective Visualization Design: Leveraging the Emotional Impact of Data”, Accessed: May 17, 2025. [Online]. Available: https://affectivevis.github.io/
