import javalang
import jsondiff
import json

# Define a mapping from JSON keys to HTTP methods
method_mapping = {
    "GetMapping": "Get",
    "PutMapping": "Put",
    "PostMapping": "Post",
    "DeleteMapping": "Delete"
}

annotation_mapping = {
    "PublicAccess": "PublicAcess",
    "Authenticated": "Authenticated",
    "PermissionCheck": "PermissionCheck",
    "SecureM2M": "SecureM2M",
    "B2BPartnerCheck": "B2BPartnerCheck",
    "B2BPermissionCheck": "B2BPermissionCheck",
    "B2BFeatureToggle": "B2BFeatureToggle",
}

def extract_annotations(code):
    tree = javalang.parse.parse(code)
    annotations_dict = {}

    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        method_name = node.name
        annotations = []
        for annotation in node.annotations:
            annotation_name = annotation.name
            annotations_values = {}
            if hasattr(annotation, 'element') and annotation.element is not None:
                for element_pair in annotation.element:
                    if type(element_pair).__name__ == 'tuple':
                        element_name = 'value'
                        element_value = element_pair[-1]
                    else:
                        element_name = element_pair.name
                        element_value = element_pair.value
                    if isinstance(element_value, javalang.tree.Literal):
                        annotations_values[element_name] = element_value.value
                    elif isinstance(element_value, javalang.tree.MemberReference):
                        annotations_values[element_name] = element_value.member
                    else:
                        annotations_values[element_name] = str(element_value)
                    annotations_values[element_name] = annotations_values[element_name].replace('"', '')
            annotations.append({annotation_name: annotations_values})

        annotations_dict[method_name] = annotations

    return annotations_dict

def export_json(anno1, anno2, controllerName):
    endpoints1 = mapEndpoint(anno1, controllerName)
    endpoints_master = mapEndpoint(anno2, controllerName)
    diff = jsondiff.diff(endpoints_master, endpoints1, syntax='symmetric', marshal=True)
    if(type(diff).__name__ == 'list'):
        tempDiff = {}
        if(len(diff)>0 and len(diff[0])>0):
            tempDiff["$delete"] = diff[0]
        if(len(diff)>1 and len(diff[1])>0):
            tempDiff["$insert"] = diff[1]
        diff = tempDiff
    # with open('test1.json', 'w') as convert_file: 
    #     convert_file.write(json.dumps(endpoints1))
    # with open('test_master.json', 'w') as convert_file: 
    #     convert_file.write(json.dumps(endpoints_master))
    # with open('test_comp.json', 'w') as convert_file: 
    #     convert_file.write(json.dumps(diff))

    for key, value in diff.items():
        for k,v in value.items():
            if key == "$insert":
                v['status'] = "inserted"
                endpoints_master[k] = v

            elif key == "$delete":
                v['status'] = "deleted"
                endpoints_master[k] = v

            else:
                if(v[0] == ''):
                    endpoints_master[key][k] = f'+{v[1]}'
                elif(v[1] == ''):
                    endpoints_master[key][k] = f'-{v[0]}'
                else:
                    if(k == 'useCase'):
                        endpoints_master[key][k] = v
                    elif k == 'annotation':
                        endpoints_master[key][k] = v
                    else:
                        endpoints_master[key][k] = f'{v[0]}->{v[1]}'
    return endpoints_master.values();

def mapEndpoint(anno1, controllerName):
    endpoints = {};
    for key, value in anno1.items():

        # Check if the method is annotated with a HTTP method
        methodName = ""
        for i in method_mapping:
            for annotation in value:
                if i in annotation:
                    methodName = method_mapping[i]
                    break
            if methodName:
                break

        # Check which annotations has been used
        annotation = []
        for annotation_item in value:
            # if i in annotation_item:
            for k,v in annotation_item.items():
                annotation.append(k)

        # for i in annotation_mapping:
        #     for annotation_item in value:
        #         if i in annotation_item:
        #             annotation.append(annotation_mapping[i])

        # Extract values from annotations
        path_value = ""
        data_classification_value = ""
        use_case = []
        for annotation_item in value:
            if methodName and methodName + "Mapping" in annotation_item:
                path_value = annotation_item[methodName + "Mapping"]["value"]
            if "SecurityClassification" in annotation_item:
                data_classification_value = annotation_item["SecurityClassification"]["dataConfidentiality"]
            if "B2BPermissionCheck" in annotation_item:
                use_case.append(annotation_item["B2BPermissionCheck"]["usecase"])

        endpoints[key] = ({
            "controllerName": controllerName,
            "functionName": key,
            "method": methodName,
            "path": path_value,
            "annotation": ', '.join(annotation),
            "dataClassification": data_classification_value,
            "useCase": ', '.join(use_case)
        })
    
    return endpoints



# with open("mises/ms-oce-soe-search-b2b-customers/src/main/java/com/swisscom/oce/b2bcustomers/controller/CustomersRolesController.java", "r") as file1:
#     read_content = file1.read()
#     print(extract_annotations(read_content))
# Opening JSON file
# with open('annotations/SearchActivityController.java-10.55.0.json') as json_file:
#     a = json.load(json_file)
# with open('annotations/SearchActivityController.java-master.json') as json_file:
#     b = json.load(json_file)
# export_json(a,b, "test")