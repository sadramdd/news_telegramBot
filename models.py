from transformers import AutoConfig, AutoTokenizer, AutoModel,  AutoModelForSeq2SeqLM
import torch
from torch import nn
from peft import get_peft_model, LoraConfig, TaskType


"""
def single_summarize(sentence, summarizer_model, tokenizer, device="cpu"):
    '''
    takes a single string (the sentence) and does the embedding and
    tokenzation task with the models provided 
    device indicates cpu/gpu to train on
    '''
    inputs = tokenizer(sentence, return_tensors="pt", padding=True, truncation=True, max_length=1024).to(device)

    summarizer_model.to(device)
    summarizer_model.eval()

    with torch.inference_mode():
        summary_ids = summarizer_model.generate(**inputs,
                                                num_beams=4,
                                                early_stopping=True,
                                                min_length=128,
                                                max_length=512,
                                                length_penalty=2.0,
                                                repetition_penalty=2.0)

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


from peft import get_peft_model, LoraConfig, TaskType

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.SEQ_2_SEQ_LM
)

# model for summary
model_name = "google/mt5-small" # pretrained multilangual summarizer model hugging face path
summ_tokenizer = AutoTokenizer.from_pretrained(model_name) # loads tokenizer artitechure from hugging face
summarizer = AutoModelForSeq2SeqLM.from_pretrained(model_name) # loads pretrained multilangual summarizer from hugging face

summarizer = get_peft_model(summarizer, lora_config) #PEFT contfing

summarizer.load_state_dict(torch.load(r"/content/drive/MyDrive/mt5_persian_finetuned_weights.pth")) #loading the fine tuned model weights
"""


keyword = "HooshvareLab/bert-fa-base-uncased"
config = AutoConfig.from_pretrained(keyword)

#persian bert is the pretrained embedding model on large persian dataset
persian_bert = AutoModel.from_pretrained(keyword, config=config)
persian_bert_tokenizer = AutoTokenizer.from_pretrained(keyword)

#hugging face: https://huggingface.co/HooshvareLab/bert-fa-base-uncased
#github: https://github.com/hooshvare/parsbert



#sentiment model class def
class sentimentClassifier(nn.Module):
    def __init__(self, input_dim: int,
                 hidden_dim1: int, hidden_dim2: int,
                 output_dim:int, embedder, tokenizer):
        
        super(sentimentClassifier, self).__init__()
        
        from torch.utils.data import TensorDataset, DataLoader
        self.layer1 = nn.Linear(input_dim, hidden_dim1)
        self.act1 = nn.ReLU()
        self.layer2 = nn.Linear(hidden_dim1, hidden_dim2)
        self.act2 = nn.ReLU()
        self.layer3 = nn.Linear(hidden_dim2, output_dim)
        self.embedder = embedder
        self.tokenizer = tokenizer
        self.dataset = TensorDataset
        self.dataloader = DataLoader
        
    def forward(self, x):
        """
        inputs: 
        
        x, the embedded torch tensor for sentences

        output:

        prediction logits
        """
        output_1_withoutReLU = self.layer1(x)
        output_1 = self.act1(output_1_withoutReLU)
        output_2_withoutReLU = self.layer2(output_1)
        output_2 = self.act2(output_2_withoutReLU)
        prediction = self.layer3(output_2)
        return prediction        
    def tokenize(self,
                x: list,device: str="cpu",
                sentence_maxLength: int=50,
                batch_size: int=10):
        """
        inputs: 
        x, a list of sentences
        
        device, the device to do the tokenization task in it
        
        sentence_maxLength, length of every sentence to padd, truncate to
        
        batch_size, length of every batcg in tokenization

        output:
        
        DataLoader class of torch with structure of (input_ids, attention_mask)
        """
        
        self.embedder.to(device)
        self.embedder.eval()

        tokenized = self.tokenizer(x,
                            padding="max_length",
                            max_length=sentence_maxLength,
                            truncation=True,
                            return_tensors="pt")
        
        input_ids = tokenized["input_ids"]
        attention_mask = tokenized["attention_mask"]

        # Create a DataLoader to automatically handle batching
        dataset = self.dataset(input_ids, attention_mask)
        dataloader = self.dataloader(dataset, batch_size=batch_size)

        return dataloader
    def embedd(self, dataloader, device: str="cpu"):
        """
        inputs: 
        
        dataloader, pytorch DataLoader class with input_ids, attention_mask
        device, device to use for embedding task, (cpu or cuda)

        output: 
        
        torch tensor in shape of (dataloader_length, 768 (embedding size))
        """
        from tqdm import tqdm as progressbar
        embeddings_list = []

        with torch.inference_mode():
            for input_ids_batch, attention_mask_batch in progressbar(dataloader, desc="Embedding batches"):
                input_ids_batch = input_ids_batch.to(device)
                attention_mask_batch = attention_mask_batch.to(device)
                
                outputs = self.embedder(input_ids=input_ids_batch, attention_mask=attention_mask_batch)
                cls_embeddings = outputs.pooler_output.cpu()
                embeddings_list.append(cls_embeddings)

        ready_x = torch.cat(embeddings_list, dim=0)
        return ready_x
    def predict(self,x: str,
                device: str="cpu",
                return_soft_fa_prediction: bool=False,
                return_soft_en_prediction: bool=False):
        if return_soft_en_prediction and return_soft_fa_prediction:
            raise ValueError("Only one of 'return_soft_fa_prediction' or 'return_soft_en_prediction' can be True.")
        """
        input: 
        
        x, as a single string representing the sentence
        device, the device to do the full prediction task in it
        return_soft_fa_prediction, decides that function returns persian soft predciton or not
        return_soft_en_prediction, decides that function returns english soft prediction or not
        
        output:

        a single integer representing the classified mode, {0: "negative", 1: "positive"} or,
        a str representing 'positive' or 'negative' in english or,
        a str representing 'positive' or 'negative' in persian
        """
        self.to(device)
        self.eval()
        decode_list = ["negative", "positive"]
        with torch.inference_mode():
            tokenized = self.tokenize([x], device=device)
            embedded = self.embedd(tokenized, device=device)
            pred = self.forward(embedded)
            prediction_rounded = round(torch.sigmoid(pred).squeeze().item())
        if return_soft_en_prediction:
            return decode_list[prediction_rounded] 
        elif return_soft_fa_prediction:
            if prediction_rounded == 0:
                return "منفی"
            return "مثبت"
        else:
            return prediction_rounded

sentiment_model = sentimentClassifier(768, 128, 64, 1, persian_bert, persian_bert_tokenizer)

sentiment_model.load_state_dict(torch.load(r"telegram_bot_project/telegram_sentiment_model_weights.pth"))