import json
import numpy as np
import evaluate
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer
)

MODEL_NAME = "DeepPavlov/rubert-base-cased"
DATASET_PATH = "resume_dataset.json"
OUTPUT_DIR = "./rubert_resume_ner"

with open(DATASET_PATH, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

all_labels = set()

for item in raw_data:
    for _, label in item["tokens"]:
        all_labels.add(label)

label_list = sorted(list(all_labels))

label2id = {label: idx for idx, label in enumerate(label_list)}
id2label = {idx: label for label, idx in label2id.items()}

dataset_dict = {
    "tokens": [],
    "ner_tags": []
}

for item in raw_data:
    tokens = []
    tags = []
    for token, label in item["tokens"]:
        if token.strip() == "":
            continue
        tokens.append(token)
        tags.append(label2id[label])
    dataset_dict["tokens"].append(tokens)
    dataset_dict["ner_tags"].append(tags)

dataset = Dataset.from_dict(dataset_dict)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        is_split_into_words=True,
        padding="max_length",
        max_length=256
    )

    labels = []

    for i, label_cycle in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label_cycle[word_idx])
            else:
                current_label = label_cycle[word_idx]
                current_label_name = id2label[current_label]

                if current_label_name.startswith("B-"):
                    inside_label = current_label_name.replace("B-", "I-")
                    if inside_label in label2id:
                        label_ids.append(label2id[inside_label])
                    else:
                        label_ids.append(current_label)
                else:
                    label_ids.append(current_label)

            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

dataset = dataset.train_test_split(test_size=0.1)

train_dataset = dataset["train"].map(
    tokenize_and_align_labels,
    batched=True
)

eval_dataset = dataset["test"].map(
    tokenize_and_align_labels,
    batched=True
)

model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(label_list),
    id2label=id2label,
    label2id=label2id
)

data_collator = DataCollatorForTokenClassification(tokenizer)
metric = evaluate.load("seqeval")

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    true_predictions = []
    true_labels = []

    for prediction, label_cycle in zip(predictions, labels):
        current_predictions = []
        current_labels = []
        for pred, lab in zip(prediction, label_cycle):
            if lab != -100:
                current_predictions.append(id2label[pred])
                current_labels.append(id2label[lab])
        true_predictions.append(current_predictions)
        true_labels.append(current_labels)

    results = metric.compute(
        predictions=true_predictions,
        references=true_labels
    )

    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"]
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=5,
    weight_decay=0.01,
    logging_steps=10,
    fp16=True,
    save_total_limit=2,
    load_best_model_at_end=True,
    report_to="none"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"Модель сохранена в {OUTPUT_DIR}")