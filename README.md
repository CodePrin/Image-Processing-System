### **Objective**

The main objective of this project is to build a system to efficiently process image data from CSV files. The system will:

1. Receive:- Accept CSV file containing below "Input CSV Format":

* Column 1: Serial Number
* Column 2: Product Name:- This will be a name of product against which we will store input and output images
* Column 3: Input Image URLs - In this column we will have comma separated image URLs.

<img width="737" height="376" alt="image" src="https://github.com/user-attachments/assets/ba0cdeff-01d2-470b-aaf9-de6db06dcb4f" />




2\. Validate:- Ensure the CSV data is correctly formatted.



3\. Process:- Asynchronously process images which means the image will be compressed by 50% of its original quality.



4\. Store:- Save processed image data and associated product information to a database.

5. Respond:-

a. Initially:- Provide a unique request ID to the user immediately after file submission.

b. Later:- Offer a separate API to check processing status using the request ID.




## **Requirements**

**1. Asynchronous Processing:-**

* Upload API: Accepts the CSV, Validate the Formatting and returns a unique request ID.
* Status API: Allows users to query processing status with the request ID.
* Bonus Point: Create a webhook flow so that after processing all the images you can trigger the webhook endpoint.



**2. Output CSV Format:-**

* Column 1: Serial Number
* Column 2: Product Name:- This will be a name of product against which we will store input and output images.
* Column 3: Input Image URLs:- In this column we will have comma separated image URLs.
* Column 4: Output Image URLs:- In this column we will have comma separated output image URLs in the same sequence as input.

<img width="838" height="543" alt="image" src="https://github.com/user-attachments/assets/92fa10bf-2197-4ed4-94f6-f814f2318496" />



**3. Low-Level Design (LLD):-**

* Create a detailed technical design document.
* Include a visual diagram of the system (using Draw.io or similar).
* Describe the role and function of each component.



**4. Components to Include:-**

* Image Processing Service Interaction: Integrate with the async image processing service.
* Webhook Handling: Process callbacks from the image processing service.
* Database Interaction: Store and track the status of each processing request.



**5. API Endpoints:-**

* Upload API: Accept CSV files and return a unique request ID.
* Status API: Check the processing status using the request ID.



**6. Database Schema:-**

* Design a database schema to store product data and track the status of each processing request.
* API Documentation: Clear specifications for API Documentation.
* Asynchronous Workers Documentation: Description of worker functions.
* GitHub Repository: Containing all project code.
* Postman Collection: Publicly accessible link for testing the APIs.



**7. Tech Stack:-** 

Use NodeJS or Python



**8. Databases:-** 

Use SQL or NoSQL





### **Tools \& Technologies Used**

* Python
* SQL (SQLite)
* blinker==1.9.0
* certifi==2025.10.5
* charset-normalizer==3.4.4
* click==8.3.0
* colorama==0.4.6
* Flask==3.1.2
* idna==3.11
* itsdangerous==2.2.0
* Jinja2==3.1.6
* MarkupSafe==3.0.3
* numpy==2.3.3
* pandas==2.3.3
* pillow==11.3.0
* python-dateutil==2.9.0.post0
* pytz==2025.2
* requests==2.32.5
* six==1.17.0
* tzdata==2025.2
* urllib3==2.5.0
* Werkzeug==3.1.3





### **Process Flow**



**1. CSV Upload**

* The user uploads a CSV via /upload\_csv endpoint.
* CSV is validated for required columns:

\['Serial Number', 'Product Name', 'Input Image URLs]

* A unique request\_id is generated and stored in the requests table.



**2. Asynchronous Processing**

* A background thread (Thread-Pool Executor) is started.
* The thread reads the CSV and processes each row independently.
* For each image URL:

The URL is validated and converted if needed (GitHub/Drive direct links).

The image is downloaded, resized, and compressed (50% quality).

The processed image is saved in the processed\_images/ folder.



**3. Database Operations**

* Every processed image and its details are inserted into the products table.
* Fields include:

serial\_number, product\_name, input\_image\_urls, output\_image\_urls, status.

* The request’s progress and final outcome are stored in the requests table.



**4. Output Generation**

Once processing is completed:

* All results are saved into an output.csv file.
* The requests table status is updated to Completed with total rows processed



**5. Monitoring \& Webhook**

* The user can track the processing using:

/request\_status/<request\_id> — returns live status, message, and row count.

* If a webhook\_url is provided, the system automatically notifies the external service once processing completes.



**6. Serving Processed Files**

* Processed images are publicly accessible via:

/processed\_images/<filename> route.

* The output.csv can be downloaded directly from the server directory and it is generated in CSV format also.




## **Diagram**

![Flowchart](https://github.com/user-attachments/assets/1830d358-fbd3-4d35-a28c-fff47c34db62)





## **Result**
A fully functional Flask-based Image Processing API capable of:

* Validating CSV input.
* Downloading and processing images efficiently.
* Tracking and storing request status in a database.
* Sending automated completion notifications via webhook.



