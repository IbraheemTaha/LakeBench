<div>
    <h1>LSH Ensemble</h1>
</div>


<br>

<h2>Folder Structure</h2>

```
.
├─── pretrain.py             # Pretrain
├─── index.py                # Index the columns of tables
├─── query.py                # Get the union results                         
├─── hnsw_search.py     
└─── lsh.md
```

<br>

<h2>Training Steps</h2>

**Step1: Check your environment**

You need to properly install nvidia driver first. To use GPU in a docker container You also need to install nvidia-docker2 ([Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)). Then, Please check your CUDA version via `nvidia-smi`

**Step2: Pretrain**

```sh
#webtable
python pretrain.py --c config/pretrain/webtable/lsh.yaml
#opendata
python pretrain.py --c config/pretrain/opendata/lsh.yaml
```

**Step3: Indexing**

```sh
#webtable
python index.py --c config/index/webtable/lsh.yaml
#opendata
python index.py --c config/index/opendata/lsh.yaml
```

**Step4: Querying**

```sh
#webtable
python query.py --c config/query/webtable/lsh.yaml
#opendata
python query.py --c config/query/opendata/lsh.yaml
```