# Friender

A full-stack Tinder-like clone that allows users to find friends in their geographic area. Users can swipe yes/no, see a list of their friends, and log in/log out.

This repo contains the Flask backend, the React frontend can be found <a href="https://github.com/celestekilgore/friender-frontend">here</a>.

## Live Demo

Here is a [demo](https://friend-er.surge.sh/) of Friender. 

Feel free to use 'testuser' and 'password' to log in, or create your own account! (Most of the sample users uses the zip code 04106)

This is hosted using a free service so please give the server a few minutes to warm up. 

### Technologies
- React
- Flask
- AWS S3
- Bootstrap
- PostgreSQL
- JSON Web Token
- bcrypt

## Features
Here is an overview of some of the key features

- Users can create an account, log in, and log out.
- Users can swipe yes or no on other users.
- If two users both swipe yes, they're a match! They will then appear in each other's "friends" list.
- If either user swipes no, the two users won't see each other again.
- Utilizes an AWS S3 bucket to efficiently store user’s profile pictures.

### To-do
- Implement the messaging feature.
- Add testing. 
