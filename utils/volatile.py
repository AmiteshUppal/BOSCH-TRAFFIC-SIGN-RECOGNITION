import os
import random
import shutil
import pandas as pd
import json

def create_dir(file_dir):
    if os.path.exists(file_dir):
        shutil.rmtree(file_dir)
        os.mkdir(file_dir)
    elif not os.path.exists(file_dir):
        os.mkdir(file_dir)

def name_split(data_req):
    data_df = []
    for data in data_req:
        path = data[0]
        class_name = data[1]
        img = data[2]
        img_name, ext = img.split(".")
        data_df.append([path, class_name, img_name, ext])
    df = pd.DataFrame(
        data_df, columns=["Path", "Class Name", "Image Name", "Extension"]
    )
    return df

def save_modified(image_df, modified_loc):    
    class_list = image_df["Class Name"].unique()
    for class_name in class_list:
        dir_path = os.path.join(modified_loc, str(class_name))
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        rows = image_df.loc[image_df["Class Name"] == str(class_name)]
        paths = rows["Path"].values.tolist()
        class_names = rows["Class Name"].values.tolist()
        img_names = rows["Image Name"].values.tolist()
        ext = rows["Extension"].values.tolist()
        for i in range(len(paths)):
            org_loc = paths[i]
            file_name = str(img_names[i]) + "." + ext[i]
            new_loc = os.path.join(modified_loc, str(class_names[i]), file_name)
            shutil.copy2(org_loc, new_loc)

def create_json_file(root_dir, output_name):
    NUM_CLASSES = 43
    json_dict = {}
    class_object_list = []
    for _, classes, _ in os.walk(root_dir, topdown=True):
        for class_name in classes:
            class_dict = {}
            class_dict["name"] = class_name
            path = os.path.join(root_dir, class_name)
            class_dict["path"] = path
            if int(class_name) < NUM_CLASSES:
                modified = "false"
            else:
                modified = "true"
            img_object_list = []
            for _, _, images in os.walk(path, topdown=True):
                for img_name in images:
                    img_dict = {}
                    img_dict["name"] = img_name
                    path_img = os.path.join(path, img_name)
                    img_dict["path"] = path_img
                    img_dict["can_be_modified"] = modified
                    img_dict["selected"] = "true"
                    img_object_list.append(img_dict)
            class_dict["images"] = img_object_list
            class_object_list.append(class_dict)
    class_object_list_sort = sorted(class_object_list, key = lambda i: int(i['name']))
    json_dict["folders"] = class_object_list_sort
    out_path = os.path.join(root_dir, output_name)
    with open(out_path, 'w') as json_file:
        json.dump(json_dict, json_file)

def create_original_json():
    loc_path = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.join(loc_path, '..', 'data', 'original')
    output_name = 'structure.json'
    create_json_file(root_dir, output_name)
    return os.path.join(root_dir, output_name)

def read_modified_json(json_data):
    data_req = []
    mod_dict = json.loads(json_data)
    for class_dict in mod_dict["folders"]:
        class_name = class_dict["name"]
        for img_dict in class_dict["images"]:
            if img_dict["selected"] == "true":
                img_name = img_dict["name"]
                img_path = img_dict["path"]
                data_req.append((img_path, class_name, img_name))
    return data_req

def transfer_to_modified(json_data):
    loc_path = os.path.dirname(os.path.realpath(__file__))
    modified_loc = os.path.join(loc_path, "..", "data", "modified")
    create_dir(modified_loc)
    data_req = read_modified_json(json_data)
    image_df = name_split(data_req)
    save_modified(image_df, modified_loc)

def get_train_percentage(json_data):
    percent_dict = json.loads(json_data)
    train_percent = int(percent_dict["training_data"])
    fraction = train_percent/100
    return fraction

def split_images(root_dir, train_dir, test_dir, train_fraction):
    for _, classes, _ in os.walk(root_dir):
        for class_name in classes:
            train_dir_path = os.path.join(train_dir, str(class_name))
            test_dir_path = os.path.join(test_dir, str(class_name))
            if not os.path.exists(train_dir_path): 
                os.mkdir(train_dir_path)
            if not os.path.exists(test_dir_path): 
                os.mkdir(test_dir_path)
            path = os.path.join(root_dir, str(class_name))
            for _, _, images in os.walk(path):
                num_images = len(images)
                num_train = int(train_fraction*num_images)
                train_images = random.sample(images, num_train)
                test_images = [img for img in images if img not in train_images]
                for img_name in train_images:
                    path_img = os.path.join(path, img_name)
                    org_loc = path_img
                    new_loc = os.path.join(train_dir_path, str(img_name))
                    shutil.copy2(org_loc, new_loc)
                for img_name in test_images:
                    path_img = os.path.join(path, img_name)
                    org_loc = path_img
                    new_loc = os.path.join(test_dir_path, str(img_name))
                    shutil.copy2(org_loc, new_loc)

def transfer_to_split(json_data):
    loc_path = os.path.dirname(os.path.realpath(__file__))
    modified_loc = os.path.join(loc_path, "..", "data", "modified")
    split_train_loc = os.path.join(loc_path, "..", "data", "split", "train")
    split_test_loc = os.path.join(loc_path, "..", "data", "split", "test")
    create_dir(split_train_loc)
    create_dir(split_test_loc)
    fraction = get_train_percentage(json_data)
    split_images(modified_loc, split_train_loc, split_test_loc, fraction)

def create_train_test_json():
    main_dict = {}
    loc_path = os.path.dirname(os.path.realpath(__file__))
    train_dir = os.path.join(loc_path, '..', 'data', 'split', 'train')
    test_dir = os.path.join(loc_path, '..', 'data', 'split', 'test')
    create_json_file(train_dir, 'train.json')
    create_json_file(test_dir, 'test.json')
    train_json = os.path.join(train_dir, 'train.json')
    with open(train_json) as f:
        train_dict = json.load(f)
    train_data = json.dumps(train_dict)
    test_json = os.path.join(test_dir, 'test.json')
    with open(test_json) as f:
        test_dict = json.load(f)
    test_data = json.dumps(test_dict)
    main_dict["train"] = train_data
    main_dict["test"] = test_data
    return main_dict

def select_random_batch(root_dir, file_dir, select_fraction):
    final_dir = os.path.join(root_dir, '..', 'data', 'aug_trans')
    create_dir(final_dir)
    for _, classes, _ in os.walk(file_dir):
        for class_name in classes:
            path = os.path.join(file_dir, str(class_name))
            for _, _, images in os.walk(path):
                num_images = len(images)
                num_select = int(select_fraction*num_images)
                select_images = random.sample(images, num_select)
                for img_name in select_images:
                    org_loc = os.path.join(path, img_name)
                    new_loc = os.path.join(final_dir, img_name)
                    shutil.copy2(org_loc, new_loc)

def create_random_batch(folder, percent):
    loc_path = os.path.dirname(os.path.realpath(__file__))
    modified_loc = os.path.join(loc_path, "..", "data", "modified")
    split_train_loc = os.path.join(loc_path, "..", "data", "split", "train")
    split_test_loc = os.path.join(loc_path, "..", "data", "split", "test")
    if folder == "train":
        file_dir = split_train_loc
    elif folder == "test":
        file_dir = split_test_loc
    elif folder == "complete":
        file_dir = modified_loc
    fraction = percent/100
    select_random_batch(loc_path, file_dir, fraction)

def create_manual_batch(data):
    root_dir = os.path.dirname(os.path.realpath(__file__))
    final_dir = os.path.join(root_dir, '..', 'data', 'aug_trans')
    create_dir(final_dir)
    mod_dict = json.loads(data)
    for img_dict in mod_dict["images"]:
        img_name = img_dict["name"]
        org_loc = img_dict["path"]
        new_loc = os.path.join(final_dir, img_name)
        shutil.copy2(org_loc, new_loc)

def create_trial_json():
    loc_path = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.join(loc_path, "..", "data", "modified")
    json_dict = {}
    img_object_list = []
    for _, classes, _ in os.walk(root_dir, topdown=True):
        for class_name in classes:
            path = os.path.join(root_dir, class_name)
            for _, _, images in os.walk(path, topdown=True):
                for img_name in images:
                    img_dict = {}
                    img_dict["name"] = img_name
                    path_img = os.path.join(path, img_name)
                    img_dict["path"] = path_img
                    img_object_list.append(img_dict)
    json_dict["images"] = img_object_list
    return json_dict