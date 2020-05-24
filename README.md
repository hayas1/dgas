# Distributed Graph Algorithm Simulator

分散アルゴリズムのシミュレーションを行う


# usage
## 静的ネットワーク
Developing...

## 動的ネットワーク
node.Nodeやnode.LoggingNodeを継承したクラスを作成する。
manet.field.init_random()でノードが初期配置されたフィールドのインスタンスを得る。
daemon.ManetDaemon()でシミュレーションを行うデーモンのインスタンスを得る。

アニメーションはdaemon.animation()、
シミュレーションだけをするときはdaemon.main_loop()を実行する。


# dependencies
pytorch, networkx, numpy, pandas
