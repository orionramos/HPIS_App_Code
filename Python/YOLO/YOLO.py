from ultralytics import YOLO

# Load the YOLO11 model
model = YOLO("yolo11n.pt")

# Export the model to ONNX format
model.export(format="onnx ")  # creates 'yolo11n.onnx'

# # Load the exported ONNX model
# onnx_model = YOLO("yolo11n.onnx")

# # Run inference
# results = onnx_model("https://ultralytics.com/images/bus.jpg")


# import cv2
from ultralytics import YOLO
from PIL import Image

img_pth = "tes1orion.jpg"
model = YOLO("yolov8n.pt") 
results = model(source=0,show=True)
res_plotted = results[0].plot()


# Show the results
for r in results:
    im_array = r.plot()  # plot a BGR numpy array of predictions
    im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
    im.show()  # show image
    im.save('results2.jpg')  # save image

# from ultralytics import YOLO

# # Load a model
# model = YOLO('yolov8n-seg.pt')  # load an official model


# # Predict with the model
# results = model('https://ultralytics.com/images/bus.jpg')  # predict on an image
# # Show the results
# for r in results:
#     im_array = r.plot()  # plot a BGR numpy array of predictions
#     im = Image.fromarray(im_array[..., ::-1])  # RGB PIL image
#     im.show()  # show image
#     im.save('results.jpg')  # save image