'''
Define all neural networks used in photo-geometric pipeline
Any learnable parameters shouldn't be defined out of this file
'''
import torch
import torch.nn as nn

# network architecture for viewpoint, lighting
class Encoder(nn.Module):
    def __init__(self, cout):
        '''
        * view: cout = 6
        * lighting: cout = 4
        '''
        super(Encoder, self).__init__()

        # encoder network
        encoder = [
            nn.Conv2d(3, 32, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=4, stride=1, padding=0),
            nn.ReLU(),
            nn.Conv2d(256, cout, kernel_size=1, stride=1, padding=0),
            nn.Tanh()
        ]
        self.encoder = nn.Sequential(*encoder)

    def forward(self, input):
        out = self.encoder(input)

        return out

# network architecture for depth, albedo
class AutoEncoder(nn.Module):
    def __init__(self, cout):
        '''
        * depth: cout=1
        * albedo: cout=3
        '''
        super(AutoEncoder, self).__init__()

        # encoder network
        encoder = [
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),       # layer 1
            nn.GroupNorm(16, 64),
            nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),      # layer 2
            nn.GroupNorm(32, 128),
            nn.LeakyReLU(0.2),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),      # layer 3
            nn.GroupNorm(64, 256),
            nn.LeakyReLU(0.2),
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),      # layer 4
            nn.LeakyReLU(0.2),
            nn.Conv2d(512, 256, kernel_size=4, stride=1, padding=0),      # layer 5
            nn.ReLU()
        ]

        # decoder network
        decoder = [
            nn.ConvTranspose2d(256, 512, kernel_size=4, stride=1, padding=0),
            nn.ReLU(),
            nn.Conv2d(512, 512, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU(),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),

            nn.Upsample(scale_factor=2),
            
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=5, stride=1, padding=2),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, cout, kernel_size=5, stride=1, padding=2),
            nn.Tanh()
        ]

        self.encoder = nn.Sequential(*encoder)
        self.decoder = nn.Sequential(*decoder)

    def forward(self, input):
        out = self.encoder(input)
        out = self.decoder(out)

        return out

    
# network architecture for confidence map
class Conf_Conv(nn.Module):
    def __init__(self):
        '''
        `Conf_Conv` outputs two pairs of confidence maps at different
        spatial resolutions for i) photometric and ii) perceptual losses
        '''
        super(Conf_Conv, self).__init__()
        encoder = [
            nn.Conv2d(3, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.LeakyReLU(0.2),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.LeakyReLU(0.2),
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.LeakyReLU(0.2),
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2),
            nn.Conv2d(512, 128, kernel_size=4, stride=1, padding=0),
            nn.ReLU()
        ]

        decoder_1 = [
            nn.ConvTranspose2d(128, 512, kernel_size=4, stride=1, padding=0),
            nn.ReLU(),
            nn.ConvTranspose2d(512, 256, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(64, 256),
            nn.ReLU(),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(32, 128),
            nn.ReLU()
        ]

        out_1 = [
            nn.Conv2d(128, 2, kernel_size=3, stride=1, padding=1),
            nn.Softplus()
        ]

        decoder_2 = [
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.ConvTranspose2d(64, 64, kernel_size=4, stride=2, padding=1),
            nn.GroupNorm(16, 64),
            nn.ReLU(),
            nn.Conv2d(64, 2, kernel_size=5, stride=1, padding=2),
            nn.Softplus()
        ]

        self.encoder = nn.Sequential(*encoder)
        self.decoder_1 = nn.Sequential(*decoder_1)
        self.out_1 = nn.Sequential(*out_1)
        self.decoder_2 = nn.Sequential(*decoder_2)

    def forward(self, input):
        out = self.encoder(input)
        out = self.decoder_1(out)
        out_1 = self.out_1(out)
        out_2 = self.decoder_2(out)
        
        return out_1, out_2
