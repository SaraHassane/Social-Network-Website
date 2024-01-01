from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User, Post, Follow, Like

def unLike(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    post.likes -= 1
    post.save()
    return JsonResponse({"message": "Unliked Post"})


def like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newlike = Like(user=user, post=post)
    newlike.save()
    post.likes += 1
    post.save()
    return JsonResponse({"message": "Liked Post"})


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        editPost = Post.objects.get(pk=post_id)
        editPost.content = data["content"]
        editPost.save()
        return JsonResponse({"message": "Changes Saved", "data": data["content"]})


def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    # Pagination
    paginator = Paginator(allPosts, 10)
    pageNumber = request.GET.get('page')
    pagePosts = paginator.get_page(pageNumber)

    allLikes = Like.objects.all()
    
    postsLiked = []
    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                postsLiked.append(like.post.id)
    except:
        postsLiked = []

    return render(request, "network/index.html", {
        "allPosts": allPosts,
        "pagePosts": pagePosts,
        "postsLiked": postsLiked
    })

def newPost(request):
    if request.method == "POST":
        content = request.POST['content']
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
        

def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(user=user).order_by("id").reverse()

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_followed=user)

    try:
        checkFollowing = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(checkFollowing) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False    

    # Pagination
    paginator = Paginator(allPosts, 10)
    pageNumber = request.GET.get('page')
    pagePosts = paginator.get_page(pageNumber)

    return render(request, "network/profile.html", {
        "allPosts": allPosts,
        "pagePosts": pagePosts,
        "username": user.username,
        "following": following,
        "followers": followers,
        "isFollowing": isFollowing,
        "user_profile": user
    })

def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followedUsers = Follow.objects.filter(user=currentUser)
    allPosts = Post.objects.all().order_by('id').reverse()

    followedPosts = []

    for post in allPosts:
        for person in followedUsers:
            if person.user_followed == post.user:
                followedPosts.append(post)
    
    # Pagination
    paginator = Paginator(followedPosts, 10)
    pageNumber = request.GET.get('page')
    pagePosts = paginator.get_page(pageNumber)

    return render(request, "network/following.html", {
        "pagePosts": pagePosts
    })



def follow(request):
    userfollow = request.POST['userfollow']
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow(user=currentUser, user_followed=userfollowData)
    f.save()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def unfollow(request):
    userfollow = request.POST['userfollow']
    currentUser = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow.objects.get(user=currentUser, user_followed=userfollowData)
    f.delete()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
