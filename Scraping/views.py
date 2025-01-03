from django.shortcuts import render, HttpResponse,redirect, get_object_or_404
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
from .forms import RegistrationForm
from amazon_flipkart_analysis import (
    Search_Product,
    Amazon_Scraping,
    Flipkart_Scraping,
    Cleaned_Data_Frames,
    Flipkart_Amazon_Analysis
)
from .models import ProductDetails
import os
from django.conf import settings
import matplotlib.pyplot as plt
from django.contrib.auth.decorators import login_required
# Create your views here.

def Home(request):
    return render(request,'index.html')

def AboutUs(request):
    return render(request,'about.html')

@login_required(login_url='login')
def Dashboard(request):
    history = ProductDetails.objects.filter(user=request.user).order_by('-created_at')
    selected_product = None
    if 'view_product_id' in request.GET:
        try:
            # Retrieve the selected product details based on the ID passed in the query string
            selected_product_id = request.GET['view_product_id']
            selected_product = get_object_or_404(ProductDetails, id=selected_product_id, user=request.user)
        except ProductDetails.DoesNotExist:
            selected_product = None
    context = {
        'history':history,
        'selected_product':selected_product,
    }
    if request.method == 'POST':
        if 'product_name' in request.POST:
            product_name = request.POST.get('product_name')
            if product_name:
                try:
                    # Get search URLs for both platforms
                    amazon_url, flipkart_url = Search_Product(product_name)
                    
                    # Scrape data from both platforms
                    amazon_df = Amazon_Scraping(amazon_url, product_name)
                    flipkart_df = Flipkart_Scraping(flipkart_url, product_name)

                    if amazon_df is not None and flipkart_df is not None:
                        # Clean the dataframes
                        amazon_cleaned, flipkart_cleaned = Cleaned_Data_Frames(amazon_df, flipkart_df)

                        # Initialize analyzer
                        analyzer = Flipkart_Amazon_Analysis(amazon_cleaned, flipkart_cleaned)

                        # Generate stats and files
                        amazon_stats, flipkart_stats = analyzer.show_price_stats()

                        # Generate and save the price comparison CSV
                        csv_filename = f"{product_name}_price_comparison.csv"
                        csv_path = os.path.join(settings.MEDIA_ROOT, f'user_media/{request.user.username}/csv/', csv_filename)
                        os.makedirs(os.path.dirname(csv_path), exist_ok=True)  # Ensure directory exists
                        analyzer.compare_price().to_csv(csv_path, index=False)
                        
                        csv_path = os.path.join(settings.MEDIA_ROOT, f'user_media/{request.user.username}/csv/', f'{product_name}_amazon_data.csv')
                        amazon_df.to_csv(csv_path,index=False)                        
                        
                        csv_path = os.path.join(settings.MEDIA_ROOT, f'user_media/{request.user.username}/csv/', f'{product_name}_flipkart_data.csv')
                        flipkart_df.to_csv(csv_path,index=False)
                        # Generate and save the price distribution chart
                        chart_filename = f"{product_name}_chart.png"
                        chart_path = os.path.join(settings.MEDIA_ROOT, f'user_media/{request.user.username}/charts/', chart_filename)
                        os.makedirs(os.path.dirname(chart_path), exist_ok=True)  # Ensure directory exists
                        fig = analyzer.show_price_comparison()
                        fig.savefig(chart_path)
                        plt.close(fig)  
                        
                        # Save data to the database
                        ProductDetails.objects.create(
                            user=request.user,
                            product_name=product_name,
                            price_comparison=f'user_media/{request.user.username}/csv/{csv_filename}',
                            price_distribution_chart=f'user_media/{request.user.username}/charts/{chart_filename}',
                            amazon_data = f'user_media/{request.user.username}/csv/{product_name}_amazon_data.csv',
                            flipkart_data =f'user_media/{request.user.username}/csv/{product_name}_flipkart_data.csv',
                            amazon_stats=amazon_stats,
                            flipkart_stats=flipkart_stats,
                        )

                        messages.success(request,f"Analysis for '{product_name}' has been saved successfully.")
                    else:
                        context['error'] = "Failed to scrape data from one or both platforms."

                except Exception as e:
                    context['error'] = f"An error occurred: {str(e)}"
        elif 'product_id' in request.POST:
            product_id = request.POST['product_id']
            if product_id:
                product =get_object_or_404(ProductDetails,id=product_id)
                product.delete()
                messages.success(request,f"History Deleted Sucessfully..")

        return redirect('dashboard')

    return render(request, 'dashboard.html', context)

def Register(request):
    if request.method=="POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user=form.save()
            login(request,user)
            messages.success(request,"User Created Successfully.")
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request,'register.html',context={'form':form})

def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            messages.success(request,"Logged In.")
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request,'login.html')
            
def Logout(request):
    logout(request)
    messages.warning(request,'Logged Out.')
    return redirect('home')
        