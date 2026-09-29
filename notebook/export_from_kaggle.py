"""
Run these lines at the END of your Kaggle notebook (after training) to export
the model so it can be downloaded and dropped into this project's model/ folder.

1. Save the model:
       model.save("papaya_model.h5")

2. In the Kaggle notebook UI: click "Save Version" -> the .h5 file will appear
   under the "Output" tab of that notebook version once it finishes running.
   Download it from there.

3. IMPORTANT — check your class order:
   If you used image_dataset_from_directory or ImageDataGenerator.flow_from_directory,
   print the class order it detected and make sure disease_info.py's CLASS_NAMES
   list matches EXACTLY (same order):

       # e.g. for image_dataset_from_directory
       print(train_ds.class_names)

       # e.g. for ImageDataGenerator
       print(train_generator.class_indices)

4. Check the input size your model expects (e.g. 224x224, 150x150) and make sure
   IMG_SIZE in app.py matches it.

5. Copy the downloaded papaya_model.h5 into: papaya-disease-app/model/papaya_model.h5
"""
