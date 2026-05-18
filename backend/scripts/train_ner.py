import json
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer
from transformers import DataCollatorForTokenClassification
from sklearn.model_selection import train_test_split

MODEL_NAME = "DeepPavlov/rubert-base-cased"
DATASET_PATH = "resume_dataset.json"
OUTPUT_DIR = "./rubert-ner-resume"
BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 2e-5

UNIQUE_LABELS = [
    "O", "B-NAME", "I-NAME", "B-EMAIL", "B-PHONE", "B-DATE", "I-DATE",
    "B-SKILL", "I-SKILL", "B-POS", "I-POS", "B-ORG", "I-ORG",
    "B-EDU", "I-EDU", "B-LOC", "I-LOC", "B-ACHIEVEMENT", "I-ACHIEVEMENT"
]

label2id = {label: i for i, label in enumerate(UNIQUE_LABELS)}
id2label = {i: label for label, i in label2id.items()}

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


class ResumeDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=256):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        token_label_pairs = item["tokens"]
        tokens = []
        raw_labels = []
        for pair in token_label_pairs:
            if isinstance(pair, (list, tuple)):
                tokens.append(str(pair[0]))
                raw_labels.append(str(pair[1]))
            else:
                tokens.append(str(pair))

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )

        word_ids = encoding.word_ids()
        aligned_labels = []
        for word_id in word_ids:
            if word_id is None:
                aligned_labels.append(-100)
            else:
                label = raw_labels[word_id] if word_id < len(raw_labels) else "O"
                aligned_labels.append(label2id.get(label, 0))

        encoding["labels"] = torch.tensor(aligned_labels)
        return {k: v.squeeze(0) for k, v in encoding.items()}


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def train():
    print("Загрузка датасета")
    data = load_dataset(DATASET_PATH)
    train_data, val_data = train_test_split(data, test_size=0.1, random_state=42)
    print(f"Обучающая: {len(train_data)}, валидационная: {len(val_data)}")

    train_dataset = ResumeDataset(train_data, tokenizer)
    val_dataset = ResumeDataset(val_data, tokenizer)

    print("Загрузка модели")
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(UNIQUE_LABELS),
        id2label=id2label,
        label2id=label2id
    )

    data_collator = DataCollatorForTokenClassification(tokenizer)

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=50,
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )

    print("Обучение")
    trainer.train()

    print("Сохранение")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Модель сохранена в {OUTPUT_DIR}")


if __name__ == "__main__":
    train()