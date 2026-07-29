# -*- coding: utf-8 -*-
"""
Keyword Dictionaries: Models/Algorithms, Data Modalities, Diseases/Tissues.
Also provides an interface for automatic dictionary expansion.
"""

import re

# ==================== Models / Algorithms ====================
BASE_MODEL_KEYWORDS = {
    # ========== Traditional Machine Learning ==========
    "Logistic Regression": r"\bLogistic Regression\b|\bLR\b",
    "SVM": r"\bSVM\b|\bSupport Vector Machine(?:s)?\b",
    "SVR": r"\bSVR\b|\bSupport Vector Regression\b",
    "Decision Tree": r"\bDecision Tree(?:s)?\b",
    "Random Forest": r"\bRandom Forest(?:s)?\b",
    "Extra Trees": r"\bExtra Trees\b|\bExtraTrees\b",
    "Naive Bayes": r"\bNaive Bayes\b|\bNB\b",
    "KNN": r"\bKNN\b|\bK-?Nearest Neighbors?\b",
    "K-Means": r"\bK-?Means?\b|\bKMeans?\b",
    "AdaBoost": r"\bAdaBoost\b",
    "Gradient Boosting": r"\bGradient Boosting\b|\bGBM\b|\bGBDT\b",
    "XGBoost": r"\bXGBoost\b|\bXGB\b",
    "LightGBM": r"\bLightGBM\b|\bLightGB\b",
    "CatBoost": r"\bCatBoost\b",
    "Elastic Net": r"\bElastic[- ]?Net\b",
    "Ridge Regression": r"\bRidge Regression\b",
    "LASSO": r"\bLASSO\b|\bLasso Regression\b",
    "Sparse Representation": r"\bSparse Representation\b|\bSRC\b",
    "Markov": r"\bMarkov\b|\bHMM\b|\bHidden Markov\b",
    "PCA": r"\bPCA\b|\bPrincipal Component Analysis\b",
    "LDA": r"\bLDA\b|\bLinear Discriminant Analysis\b",

    # ========== Base CNN Architectures (Version Numbers Merged) ==========
    "CNN": r"\bCNNs?\b|\bConvolutional Neural Networks?\b",
    "AlexNet": r"\bAlexNet\b",
    "ZFNet": r"\bZFNet\b",
    "VGG": r"\bVGG(?:[-_]?(?:1[1369]|19))?\b",
    "GoogleNet": r"\bGoogleNet\b|\bGoogLeNet\b",
    "Inception": r"\bInception(?:[-_]?(?:V?[1-4]|ResNetV2))?\b",
    "ResNet": r"\bResNet(?:[-_]?\d+)?\b",
    "DenseNet": r"\bDenseNet(?:[-_]?\d+)?\b",
    "Xception": r"\bXception\b",
    "MobileNet": r"\bMobileNet(?:[-_]?V?\d+)?\b",
    "ShuffleNet": r"\bShuffleNet(?:V\d+)?\b",
    "SqueezeNet": r"\bSqueezeNet(?:[._]?V?\d+(?:\.\d+)?)?\b",
    "EfficientNet": r"\bEfficientNet(?:[-_]?B?\d+)?\b",
    "NASNet": r"\bNASNet(?:[-_]?[A-Z])?\b",
    "ConvNeXt": r"\bConvNeXt(?:[-_]?(?:[TSBL]|V?\d+))?\b",
    "RegNet": r"\bRegNet(?:[-_]?[XY]\d+)?\b",
    "ResNeXt": r"\bResNeXt\b",
    "SE-Net": r"\bSE-?Net\b|\bSqueeze[- ]?and[- ]?Excitation\b",
    "CBAM": r"\bCBAM\b|\bConvolutional Block Attention\b",
    "Res2Net": r"\bRes2Net\b",
    "CoordConv": r"\bCoordConv\b|\bCoordinate Convolution\b",
    "OctConv": r"\bOctConv\b|\bOctave Convolution\b",

    # ========== Object Detection (All YOLO Versions Merged) ==========
    "YOLO": r"\bYOLO(?:[-_]?(?:v?\d+|[9]000))?(?:[-_]?tiny)?(?:s)?\b",
    "R-CNN": r"\bR-CNN\b|\bFaster R-CNN\b|\bMask R-CNN\b|\bFast R-CNN\b|\bRCNN\b",
    "SSD": r"\bSSD\b|\bSingle Shot Detector\b",
    "RetinaNet": r"\bRetinaNet\b",
    "EfficientDet": r"\bEfficientDet\b",
    "CenterNet": r"\bCenterNet\b",
    "FCOS": r"\bFCOS\b|\bFully Convolutional One-Stage\b",
    "DINO": r"\bDINO(?:v?\d)?\b",

    # ========== Semantic/Instance Segmentation ==========
    "U-Net": r"\bU-Net\b|\bUNet\b",
    "U-Net++": r"\bU-Net\+\+\b|\bUNet\+\+\b",
    "Attention U-Net": r"\bAttention U-Net\b|\bAttentionUNet\b",
    "DeepLab": r"\bDeepLab(?:[-_]?V?\d+\+?)?\b",
    "SegNet": r"\bSegNet\b",
    "PSPNet": r"\bPSPNet\b",
    "FCN": r"\bFCN\b|\bFully Convolutional Networks?\b",
    "Mask R-CNN": r"\bMask R-CNN\b|\bMask RCNN\b",
    "PANet": r"\bPANet\b|\bPath Aggregation Network\b",
    "HRNet": r"\bHRNet\b|\bHigh[- ]?Resolution Network\b",
    "OCRNet": r"\bOCRNet\b|\bObject-Contextual\b",
    "nnU-Net": r"\bnnU-?Net\b|\bnnUNet\b",
    "3D U-Net": r"\b3D U-?Net\b|\b3DUNet\b",
    "V-Net": r"\bV-?Net\b",
    "KiU-Net": r"\bKiU-?Net\b|\bKiUNet\b",
    "DoubleU-Net": r"\bDoubleU-?Net\b|\bDoubleUNet\b",
    "MultiResUNet": r"\bMultiResUNet\b",
    "UNet3+": r"\bUNet3\+\b|\bU-Net3\+\b",
    "CE-Net": r"\bCE-?Net\b|\bContext Encoder Network\b",
    "BCDU-Net": r"\bBCDU-?Net\b",
    "MedNeXt": r"\bMedNeXt\b",
    "Mamba-UNet": r"\bMamba-?UNet\b",
    "VM-UNet": r"\bVM-?UNet(?:[-_]?V?\d+)?\b|\bVMUNet(?:[-_]?V?\d+)?\b",
    "H-ViT": r"\bH-?ViT\b",
    "SegNeXt": r"\bSegNeXt\b",
    "Mask2Former": r"\bMask2Former\b",
    "MaskFormer": r"\bMaskFormer\b",
    "SAM": r"\bSAM\b|\bSegment Anything Model\b",
    "MedSAM": r"\bMedSAM\b|\bMedical SAM\b",
    "MobileSAM": r"\bMobileSAM\b",

    # ========== Transformer Family ==========
    "Transformer": r"\bTransformer(?:s)?\b",
    "ViT": r"\bViT(?:s)?\b|\bVision Transformer(?:s)?\b",
    "DeiT": r"\bDeiT\b",
    "DETR": r"\bDETR\b",
    "SegFormer": r"\bSegFormer\b",
    "Swin": r"\bSwin(?:[-_]?V?\d)?\b|\bSwin Transformer(?:s)?\b|\bSwinUNet\b",
    "PVT": r"\bPVT(?:v?\d)?\b|\bPyramid Vision Transformer(?:s)?\b",
    "CaiT": r"\bCaiT\b",
    "MobileViT": r"\bMobileViT(?:v?\d)?\b",
    "CrossViT": r"\bCrossViT\b",
    "Twins": r"\bTwins\b|\bTwins Transformer\b",
    "TNT": r"\bTNT\b|\bTransformer in Transformer\b",
    "CSWin": r"\bCSWin\b|\bCross-Shaped Window\b",
    "Focal Transformer": r"\bFocal Transformer\b",
    "DAT": r"\bDAT\b|\bDeformable Attention Transformer\b",
    "MoCo": r"\bMoCo\b|\bMomentum Contrast\b",
    "DINOv2": r"\bDINOv?\d?\b",

    # ========== Pretrained / Foundation Models ==========
    "MAE": r"\bMAE\b|\bMasked Autoencoder(?:s)?\b",
    "CLIP": r"\bCLIP\b",
    "RETFound": r"\bRETFound\b",
    "EyeCLIP": r"\bEyeCLIP\b",
    "VisionFM": r"\bVisionFM\b",
    "FLAIR": r"\bFLAIR\b",
    "MIRAGE": r"\bMIRAGE\b",
    "MetaGP": r"\bMetaGP\b",
    "MINIM": r"\bMINIM\b",
    "RetiZero": r"\bRetiZero\b",
    "OSPM": r"\bOSPM\b",
    "FMUE": r"\bFMUE\b",
    "EyeFound": r"\bEyeFound\b",
    "MultiMAE": r"\bMultiMAE\b",

    # ========== Hybrid Architectures (CNN + Transformer) ==========
    "CoAtNet": r"\bCoAtNet\b|\bCo-?Attention Network\b",
    "ConViT": r"\bConViT\b",
    "BoTNet": r"\bBoTNet\b|\bBoT-?Net\b",
    "TransUNet": r"\bTransUNet\b|\bTrans-?UNet\b",
    "SwinUNet": r"\bSwinUNet\b|\bSwin-?UNet\b",
    "TransFuse": r"\bTransFuse\b",
    "HiFormer": r"\bHiFormer\b",
    "UTNet": r"\bUTNet\b",
    "PVT-UNet": r"\bPVT-?UNet\b",
    "LE-ViT": r"\bLE-?ViT\b",
    "CvT": r"\bCvT\b|\bConvolutional Vision Transformer\b",
    "PiT": r"\bPiT\b|\bPooling-based Vision Transformer\b",

    # ========== Mamba / State Space Models ==========
    "Mamba": r"\bMamba\b|\bState Space Model\b",
    "VMamba": r"\bVMamba\b|\bVision Mamba\b",
    "ViM": r"\bViM\b|\bVision Mamba\b",
    "PlainMamba": r"\bPlainMamba\b",
    "EfficientVMamba": r"\bEfficientVMamba\b",
    "Mamba-ND": r"\bMamba-?ND\b",
    "MHS-VM": r"\bMHS-?VM\b",
    "LKM-UNet": r"\bLKM-?UNet\b",
    "H-vmunet": r"\bH-?vmunet\b|\bH-?VmUNet\b",

    # ========== Recurrent Neural Networks ==========
    "RNN": r"\bRNNs?\b|\bRecurrent Neural Networks?\b",
    "LSTM": r"\bLSTMs?\b|\bLong Short-Term Memory(?:s)?\b",
    "BiLSTM": r"\bBiLSTMs?\b|\bBidirectional LSTM(?:s)?\b",
    "GRU": r"\bGRUs?\b|\bGated Recurrent Unit(?:s)?\b",
    "BiGRU": r"\bBiGRUs?\b|\bBidirectional GRU(?:s)?\b",
    "TCN": r"\bTCNs?\b|\bTemporal Convolutional Networks?\b",

    # ========== Generative Models ==========
    "GAN": r"\bGANs?\b|\bGenerative Adversarial Networks?\b",
    "cGAN": r"\bcGAN\b|\bconditional GAN\b",
    "CycleGAN": r"\bCycleGAN\b",
    "StyleGAN": r"\bStyleGAN(?:2|3)?\b",
    "Pix2Pix": r"\bPix2Pix\b",
    "VAE": r"\bVAEs?\b|\bVariational Autoencoder(?:s)?\b",
    "Autoencoder": r"\bAutoencoder(?:s)?\b|\bAuto-Encoder(?:s)?\b",
    "Diffusion": r"\bDiffusion\b|\bDiffusion Model(?:s)?\b",
    "DDPM": r"\bDDPM\b|\bDenoising Diffusion\b",
    "Stable Diffusion": r"\bStable Diffusion\b",
    "ControlNet": r"\bControlNet\b",

    # ========== Graph Neural Networks ==========
    "GNN": r"\bGNNs?\b|\bGraph Neural Networks?\b",
    "GCN": r"\bGCNs?\b|\bGraph Convolutional Networks?\b",
    "GAT": r"\bGAT\b|\bGraph Attention Network\b",
    "GraphSAGE": r"\bGraphSAGE\b",

    # ========== Reinforcement Learning ==========
    "DBN": r"\bDBNs?\b|\bDeep Belief Networks?\b",
    "DQN": r"\bDQNs?\b|\bDeep Q-Network(?:s)?\b",
    "PPO": r"\bPPO\b|\bProximal Policy Optimization\b",
    "RL": r"\bRL\b|\bReinforcement Learning\b",

    # ========== Other Emerging Architectures ==========
    "KAN": r"\bKAN\b|\bKolmogorov-Arnold Network(?:s)?\b",
    "MLP-Mixer": r"\bMLP-?Mixer\b",
    "gMLP": r"\bgMLP\b",
    "Perceiver": r"\bPerceiver(?:s)?\b",
    "Perceiver IO": r"\bPerceiver IO\b",
    "JFT": r"\bJFT\b",
    "EfficientFormer": r"\bEfficientFormer\b",
    "PoolFormer": r"\bPoolFormer\b",
    "MOAT": r"\bMOAT\b",
    "ConvMixer": r"\bConvMixer\b",

    # ========== Classic Combinations/Variants ==========
    "ResUNet": r"\bResUNet\b|\bResNet-?UNet\b",
    "DenseUNet": r"\bDenseUNet\b|\bDenseNet-?UNet\b",
    "EfficientUNet": r"\bEfficientUNet\b|\bEfficientNet-?UNet\b",
    "VGGUNet": r"\bVGGUNet\b|\bVGG-?UNet\b",
    "ResFPN": r"\bResFPN\b|\bResNet-?FPN\b",
    "MobileSSD": r"\bMobileSSD\b|\bMobileNet-?SSD\b",
    "CSCA U-Net": r"\bCSCA U-?Net\b|\bCSCA-?UNet\b",
    "RetinaCoAt": r"\bRetinaCoAt\b",
    "SViT": r"\bSViT\b|\bSqueezeNet-?ViT\b",
}


# ==================== Data Modalities ====================
MODALITY_KEYWORDS = {
    "Fundus Photography": r"\bfundus(?:es)?\b",
    "OCT": r"\bOCT(?!A)(?:s)?\b|\boptical coherence tomography\b",
    "OCTA": r"\bOCTA(?:s)?\b|\boptical coherence tomography angiography\b",
    "Fluorescein Angiography": r"\bfluorescein angiography(?:s)?\b|\bFA(?:s)?\b",
    "SLO": r"\bSLO(?:s)?\b|\bscanning laser ophthalmoscopy\b",
    "Ultrasound": r"\bultrasound(?:s)?\b|\bultrasonography\b",
    "MRI": r"\bMRI(?:s)?\b|\bmagnetic resonance imaging\b",
    "CT": r"\bCTs?\b|\bchoroidal thickness\b",
    "Visual Field": r"\bvisual field(?:s)?\b|\bperimetry\b",
    "ERG": r"\bERG(?:s)?\b|\belectroretinography\b",
    "VEP": r"\bVEP(?:s)?\b|\bvisual evoked potential\b",
    "Clinical Text": r"\bclinical text(?:s)?\b|\bEHR(?:s)?\b|\belectronic health record(?:s)?\b|\bEMR(?:s)?\b",
    "Genomics": r"\bgenomics\b|\bgenome(?:s)?\b|\bGWAS\b",
    "Proteomics": r"\bproteomics\b|\bproteome(?:s)?\b",
    "Metabolomics": r"\bmetabolomics\b|\bmetabolome(?:s)?\b",
    "Transcriptomics": r"\btranscriptomics\b|\btranscriptome(?:s)?\b",
    "Multi-omics": r"\bmulti-omics\b|\bmultiomics\b|\bintegrated omics\b",
    "ICGA": r"\bICGA(?:s)?\b|\bindocyanine green angiography\b",
    "Adaptive Optics": r"\badaptive optic(?:s)?\b",
    "Autofluorescence": r"\bautofluorescence(?:s)?\b",
    "Wide-field Imaging": r"\bwide-field imaging(?:s)?\b",
    "Radiomics": r"\bradiomics\b",
}


# ==================== Diseases / Tissues ====================
DISEASE_KEYWORDS = {
    "Diabetic Retinopathy": r"\bdiabetic retinopathy(?:s)?\b|\bDR(?:s)?\b",
    "Glaucoma": r"\bglaucoma(?:s)?\b",
    "AMD": r"\bage-related macular degeneration(?:s)?\b|\bAMD(?:s)?\b",
    "Macular Edema": r"\bmacular edema(?:s)?\b|\bDME(?:s)?\b",
    "Retinal Vein Occlusion": r"\bvein occlusion(?:s)?\b|\bRVO(?:s)?\b",
    "Retinopathy": r"\bretinopathy(?:s)?\b",
    "Myopia": r"\bmyopia(?:s)?\b|\bhigh myopia\b",
    "Retinitis Pigmentosa": r"\bretinitis pigmentosa\b|\bRP(?:s)?\b",
    "Retinal Detachment": r"\bretinal detachment(?:s)?\b|\bRD(?:s)?\b",
    "Uveitis": r"\buveitis\b",
    "Retinopathy of Prematurity": r"\bretinopathy of prematurity\b|\bROP(?:s)?\b",
    "Diabetic Macular Edema": r"\bdiabetic macular edema(?:s)?\b|\bDME(?:s)?\b",
    "Central Serous Chorioretinopathy": r"\bcentral serous(?:s)?\b|\bCSC(?:s)?\b|\bCSCR(?:s)?\b",
    "Ocular Hypertension": r"\bocular hypertension\b|\bOHT(?:s)?\b",
    "Leber Hereditary Optic Neuropathy": r"\bLeber(?: disease)?\b|\bLHON(?:s)?\b",
    "Retinal Artery Occlusion": r"\bretinal artery occlusion(?:s)?\b|\bRAO(?:s)?\b",
    "Hypertensive Retinopathy": r"\bhypertensive retinopathy(?:s)?\b",
    "Optic Neuritis": r"\boptic neuritis\b",
    "Papilledema": r"\bpapilledema(?:s)?\b",
    "Choroidal Neovascularization": r"\bchoroidal neovascularization(?:s)?\b|\bCNV(?:s)?\b",
    "Polypoidal Choroidal Vasculopathy": r"\bpolypoidal choroidal vasculopathy\b|\bPCV(?:s)?\b",
    "Vitreous Hemorrhage": r"\bvitreous hemorrhage(?:s)?\b",
    "Stargardt Disease": r"\bStargardt(?: disease)?(?:s)?\b",
    "Best Disease": r"\bBest(?: disease)?(?:s)?\b",
}


# ==================== Automatic Expansion ====================

def is_likely_model_name(word):
    if re.search(r"[A-Z]", word):
        return True
    if re.search(r"\d", word):
        return True
    if re.search(r"[-_]", word):
        return True
    if re.search(r"[A-Z][a-z]+[A-Z]", word):
        return True
    return False


def expand_model_keywords(candidates, base_dict=None, min_len=3):
    if base_dict is None:
        base_dict = dict(BASE_MODEL_KEYWORDS)

    new_dict = dict(base_dict)
    added = []

    for phrase, _ in candidates:
        if not is_likely_model_name(phrase):
            continue
        if len(phrase) < min_len:
            continue
        key = phrase.replace(" ", "_").replace("-", "_").replace("/", "_")
        if key in new_dict:
            continue
        pattern = r"\b" + re.escape(phrase) + r"\b"
        new_dict[key] = pattern
        added.append((phrase, key))

    return new_dict, added