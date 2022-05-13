from unsup3d.train import Trainer
#from unsup3d.model import PercepLoss
from unsup3d.dataloader import CelebA
from unsup3d.renderer import *
import torch
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import torchvision.transforms as transforms
import torch.nn as nn
import numpy as np



class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN,self).__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(3, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, 1, 1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 3, 3, 1, 1),            
        )

    def forward(self, inp):
        res = self.enc(inp)
        res = nn.functional.softmax(res)

        loss = torch.mean(torch.abs(res - inp), dim = (0,1,2,3))    # test with L1 loss

        return loss



def test_image(path):
    img = mpimg.imread(path)
    imgplot = plt.imshow(img)
    
    print("img size :",img.shape)

    return img

def get_torch_image(b_size, H, W, path):
    img = test_image(path)
    img = torch.tensor(img/255, dtype = torch.float32)
    img = img.permute(2,0,1)    # set channel first
    transform = nn.Sequential(
        transforms.Resize((H,W)) ,
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
    )
    out = transform(img)
    out = out.unsqueeze(0)
    out = out.repeat(b_size,1,1,1)
    
    return out


def test_percep_0508():
    per = PercepLoss()
    path1 = "./test1.jpg"   
    path2 = "./test2.jpg"
    imgs1 = get_torch_image(13, 64, 64, path1)
    imgs2 = get_torch_image(13, 64, 64, path2)

    rand_conf = torch.abs(torch.rand(13,1,16,16))


    loss = per(imgs1, imgs2, rand_conf)

    print(loss)
    

def test_celeba_dataloader_0509():
    setting_list = ['train','val','test']
    for set in setting_list:
        CA = CelebA(setting = set)
        length =  CA.__len__()
        print("len ", set, " type dataset: ", length)

        for j in range(50):
            ind = torch.randint(0,length-1,(1,1))
            a = CA.__getitem__(ind.item())
            print(a.shape)

def test_Trainer_0509():
    simplenn = SimpleNN()
    trainer = Trainer(None, model = simplenn)
    trainer.train()

def test_depth_to_normal_v2():
    inp = torch.randn(17, 1, 64, 64)
    res2 = depth_to_normal_v2(None, inp)
    print(res2.shape)
    print(res2[0,0,:,:])

    for i in range(17):
        out = depth_to_normal(None, inp[i])
        if i == 0:
            res_org = out
        else:
            res_org = torch.cat([res_org, out], dim=0)
    
    print(res_org.shape)

    print("res2_mean: ", torch.mean(res2, dim=(0,1,2,3)))
    print("res_org_mean: ", torch.mean(res_org, dim=(0,1,2,3)))
    print("difference: ", torch.mean(res_org-res2, dim=(0,1,2,3)))
    print((res2-res_org)[0,0,:,:])


def depth_to_normal_v2(self, depth_map):
    '''
    input:
    - depth_map : B x 1 x W x H
    output:
    - normal_map : B x 3 x W x H
    '''
    B, _,  W, H = depth_map.shape 
    x_grid = torch.linspace(0, H-1, H, dtype = torch.float32)
    y_grid = torch.linspace(0, W-1, W, dtype = torch.float32)

    xx, yy = torch.meshgrid(x_grid, y_grid, indexing = 'ij')
    xx = xx.unsqueeze(0).unsqueeze(0).repeat(B, 1, 1, 1)
    yy = yy.unsqueeze(0).unsqueeze(0).repeat(B, 1, 1, 1)

    depth_x_s = torch.zeros_like(depth_map)
    depth_y_s = torch.zeros_like(depth_map)
    depth_x_s[:,:,1:W,:] = depth_map[:,:,0:W-1,:]
    depth_y_s[:,:,:,1:H] = depth_map[:,:,:,0:H-1]

    v1 = torch.cat([xx, (yy-1), depth_y_s], dim = 1)
    v2 = torch.cat([(xx-1), yy, depth_x_s], dim = 1)
    c = torch.cat([xx,yy,depth_map], dim = 1)

    d = torch.cross(v2-c, v1-c, dim = 1)
    n = d / torch.sqrt(torch.sum(d**2, dim = 1, keepdim=True))

    return n


def depth_to_normal(self, depth_map):
    '''
    - input: depth_map (size: torch.Size([1, 64, 64]))
    - output: normal_map (size: torch.Size([1, 64, 64])
    '''
    d, w, h = depth_map.shape
    normal_map = torch.zeros_like(depth_map).repeat(3, 1, 1)

    # calculate normal map from depth map
    for i in range(1, w - 1):
        for j in range(1, h - 1):
            v1 = torch.Tensor([i, j - 1, depth_map[0][i][j - 1]])
            v2 = torch.Tensor([i - 1, j, depth_map[0][i - 1][j]])
            c = torch.Tensor([i, j, depth_map[0][i][j]])

            d = torch.cross(v2 - c, v1 - c)
            n = d / torch.sqrt(torch.sum(d ** 2))
            normal_map[:, i, j] = n

    return normal_map.unsqueeze(0)


def test_gen_grid_0513():
    path1 = "./test1.jpg"   
    path2 = "./test2.jpg"
    imgs1 = get_torch_image(13, 64, 64, path1).cuda()
    imgs2 = get_torch_image(13, 64, 64, path2).cpu()

    grid1 = gen_grid(imgs1)
    grid2 = gen_grid(imgs2)

    print("grid 1 shape:", grid1.shape, "grid 1 device", grid1.device)
    print("grid 2 shape:", grid2.shape, "grid 2 device", grid2.device)
    print(grid2[0,:,0:10,0:10])


def test_matmul_0513_1():
    path1 = "./test1.jpg"   
    path2 = "./test2.jpg"
    imgs1 = get_torch_image(13, 64, 64, path1)
    imgs2 = get_torch_image(13, 64, 64, path2)

    if True:
        # test with mixed batch
        imgs1 = torch.cat([imgs1, imgs2], dim=0)
        
    K = torch.eye(3)

    print("imgs1 shape: ", imgs1.shape)
    print("K shape: ",K.shape)

    try:
        res1 = torch.matmul(K, imgs1)
        print(res1.shape)
    except RuntimeError as e:
        print("trial 1", e)

    try:
        K_t = K.unsqueeze(0).repeat(13,1,1)
        res2 = torch.matmul(K_t, imgs1)
        print(res2.shape)
    except RuntimeError as e:
        print("trial 2", e)

    try:
        K_t = K.unsqueeze(0).repeat(13,1,1).unsqueeze(-1)
        res3 = torch.matmul(K_t, imgs1)
        print(res3.shape)
    except RuntimeError as e:
        print("trial 3", e)

    try:        ######## -> selected ! only function that works porperly here!
        imgs1_t = imgs1.reshape(imgs1.shape[0],imgs1.shape[1],-1)
        res4 = torch.matmul(K, imgs1_t)
        res4 = res4.reshape(imgs1.shape[0],imgs1.shape[1],imgs1.shape[2],imgs1.shape[3])
        print(res4.shape)
        diff = res4-imgs1
        print("trial 4 diff mean: ", torch.mean(diff), "diff std: ", torch.std(diff))
    except RuntimeError as e:
        print("trial 4", e)

    try:
        imgs1_t = imgs1.reshape(imgs1.shape[0],imgs1.shape[1],-1).permute(1,0,2)
        res4 = torch.matmul(K, imgs1_t).permute(1,0,2)
        res4 = res4.reshape(imgs1.shape[0],imgs1.shape[1],imgs1.shape[2],imgs1.shape[3])
        print(res4.shape)
        diff = res4-imgs1
        print("trial 5 diff mean: ", torch.mean(diff), "diff std: ", torch.std(diff))
    except RuntimeError as e:
        print("trial 5", e)


def test_matmul_0513_2():       # to test (B x 3 x W x H) x (3 x 3)
    path1 = "./test1.jpg"   
    path2 = "./test2.jpg"
    imgs1 = get_torch_image(13, 64, 64, path1)
    imgs2 = get_torch_image(13, 64, 64, path2)

    if True:
        # test with mixed batch
        imgs1 = torch.cat([imgs1, imgs2], dim=0)
        
    K = torch.eye(3)

    print("imgs1 shape: ", imgs1.shape)
    print("K shape: ",K.shape)

    try:        ######## -> selected ! only function that works porperly here!
        imgs1_t = imgs1.reshape(imgs1.shape[0],imgs1.shape[1],-1).permute(0,2,1)
        res4 = torch.matmul(imgs1_t, K).permute(0,2,1)
        res4 = res4.reshape(imgs1.shape[0],imgs1.shape[1],imgs1.shape[2],imgs1.shape[3])
        print(res4.shape)
        diff = res4-imgs1
        print("trial 4 diff mean: ", torch.mean(diff), "diff std: ", torch.std(diff))
    except RuntimeError as e:
        print("trial 4", e)


def test_safe_matmul_0513():
    path1 = "./test1.jpg"   
    path2 = "./test2.jpg"
    imgs1 = get_torch_image(13, 64, 64, path1)
    imgs2 = get_torch_image(13, 64, 64, path2)

    if True:
        # test with mixed batch
        imgs1 = torch.cat([imgs1, imgs2], dim=0)
        
    K = torch.eye(3)

    res1 = safe_matmul(K, imgs1)
    diff = res1-imgs1
    print("trial 1 diff mean: ", torch.mean(diff), "diff std: ", torch.std(diff))

    res2 = safe_matmul(imgs1, K)
    diff = res2-imgs1
    print("trial 2 diff mean: ", torch.mean(diff), "diff std: ", torch.std(diff))

if __name__ == '__main__':
    test_batch_matmul_0513()


