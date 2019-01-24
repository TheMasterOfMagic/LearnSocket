# 基于socket与多线程的局域网CS框架

- 本项目为个人学习socket与多线程编程之练手作. 其实现了一套局域网内的客户端/服务端通信框架, 稍加扩展即可实现"局域网小游戏联机"或"局域网聊天室"等
- 所用到的库全部为官方库(也就是说不需要安装任何依赖)
    - 其中socket部分出于学习目的甚至没有用SocketServer库. 不论客户端还是服务端都完全使用socket库进行开发
	- 虽然使用了`Python`作为开发语言, 但由于只使用了必须的库, 所以其相比`C++`等底层语言来说, 除了不用通过`地址+大小`来传参以外, 大多数逻辑仍然是需要自己去实现的
- 下面会分别对程序逻辑与主要代码细节进行阐述或展示, 最后是一些我自己的体会与感悟

# 一. 程序逻辑
## 1. socket部分
- TCP/IP协议中, 一个套接字想要连接另一个套接字时, 需要知道对方的ip与端口. 然而事实上, 在大多数实际应用中, 服务端在启动后, 无需告知客户端自己的ip与端口. 比如在某些支持局域网联机的游戏里, 当一个玩家创建好"房间"后, 其他玩家在进入"大厅"时能直接看到当前已创建好的"房间", 进而直接进入该"房间", 而无需知道该房间的"ip与端口"
- 本框架中, 这一步是通过UDP广播的方式来实现的. 主要包含以下几个步骤:
    - 服务端在启动后会分别以TCP和UDP方式各在动态端口范围内(49152~65535)监听一个端口
    - 客户端在启动后会在整个动态端口范围以UDP方式广播一次
    - 服务端在收到客户端广播的包后, 会定向发送一个UDP包以告知自己所监听的TCP端口
    - 客户端根据该UDP包的来源地址与包中所给的端口来发起TCP连接
- 这样, 客户端在启动后自然能知道当前有哪些服务端在线, 进而可以让用户直接"进入房间"
- 此外, 考虑到服务端不一定总是比客户端先启动(比如玩家B先进入"大厅", 玩家A后创建"房间"), 所以服务端在启动时也会进行一次UDP广播, 以告知当前已在线的客户端自己所监听的TCP端口

## 2. 多线程部分
- 服务端在启动时, 会为TCP与UDP分别新开一个线程, 用于循环接收传入的连接或数据. 其中TCP部分在使用accept()函数接受一个传入的连接, 得到一个client socket后, 会为该client socket再开一个线程, 用于循环接收来自该client的数据. 这样多个客户端就可以同时与同一个服务端进行交互, 而不会发生阻塞了
- 客户端在启动时, 会先只为UDP新开一个线程, 用于循环接收数据. 在使用server socket连接一个服务端后, 客户端会再为该server socket新开一个线程, 用于循环接收来自该服务端的数据. 这样在接收的同时也不耽误客户端做其他的事情(比如接收并处理来自用户的输入等等)


## 3. 应用层部分
- 不论TCP payload还是UDP payload, 对于python来说都是bytes类型的变量. 所以需要一套encode与decode机制, 以便发送端将要发送的数据序列化, 接收端将收到的数据反序列化.
- 本框架中, TCP payload与UDP payload使用同一套encode/decode机制:
	- encode一个对象时, 先将其json化, 得到一个json串; 将该json串以utf-8编码, 即得encode结果
	- decode即为上述过程的逆过程
- 并且, 由于TCP为流式传输, 所以需要自己在应用层协议中指定如何分割数据流. 该框架中, 使用"载荷长度+载荷"的形式进行TCP传输. 发送方在编码好后, 用固定数量的字节记录其长度, 并将"载荷长度+载荷"作为实际发送的内容. 对应的, 接收方在接收时需接收固定数量的字节, 并将其作为载荷长度, 稍后再接收"载荷长度"个字节, 作为对方实际传输的数据
- 此外, 本框架假设所有的应用层包都为`dict`类型, 并通过一个`TYPE`字段标明该包的类型, 通过其他字段给出相应的信息. 所以正常情况下, 发送方发送的数据在编码前, 与接收方收到的数据在解码后, 都应该是一个拥有`TYPE`字段的`dict`

# 二. 主要代码细节
- 整个框架主要用到了三个类: End(终端), Client(客户端)与Server(服务端), 此外还有对`logging`模块稍加封装得到的`log.py`
- 代码中`debug()`函数出现了很多次, 它其实就是调用`log.py`中的日志记录器进行输出而已, 对程序主要逻辑没有影响. 本节将忽略所有的`debug()`函数

## 1. End

- 在[\_\_init__()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L12)中, 我们为每个End示例绑定两个套接字, 一个`tcp_socket`与一个`udp_socket`, 并对`udp_socket`进行相应设置使之可以进行广播
- `udp_socket`在服务端与客户端中的用法都是一样的, 都是用于发送和接收udp数据, 而`tcp_socket`在两个子类中的用法有所区别:
	- 在服务端, `tcp_socket`用于循环接收传入的连接, 本身并不直接用于收发tcp数据
	- 在客户端, `tcp_socket`用于发起`tcp`连接 
- 上文提到的`encode/decode`机制, 作为客户端与服务端共同遵守的内容, 也被放进了基类`End`中, 成为了[encode()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L18)与[decode()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L25). 由于上文应用层部分提到的逻辑, 这两个函数中会检查编码前与解码后的数据是否是包含`TYPE`字段的`dict`类型, 若不是则作失败处理(encode失败时返回`b''`, decode失败时返回`None`)
- [broadcast_udp()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L32), [send_udp()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L48), [recv_udp()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L65)与[handle_udp()](handle_udp)为交互过程中与udp相关的4个操作. 顾名思义, 其作用分别为广播, 定向发送, 接收与处理. 其中`recv_udp()`不能直接调用, 需要新开一个线程; `handle_udp()`则类似于一个回调函数, 在`recv_udp()`接收到数据且数据合法时[调用](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L91). 此外, 与tcp相关的3个操作(少了一个广播)也是类似的结构
- 在基类`End`中, `handle_udp()`与`handle_tcp()`中没有实际的内容, 是为了模拟虚函数. 子类应该自己实现这两个函数
- 此外, 各种tcp与udp操作中都会出现高度统一的`try...except OSError...`语句. 这是为了在套接字关闭时使这些函数或线程能正常退出而不至于报异常(若套接字已关闭, 则`socket.socket`实例的`recv()`, `accept()`等函数会引发9号OSError异常)

## 2. Client
- 由上文程序逻辑中"socket部分"与"应用层部分"提到的逻辑, 客户端在启动时会构造一个[CLIENT_HELLO包](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L164)并[广播之](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L165). 在`Server`的`handle_udp()`中, 如果[发现包类型为CLIENT_HELLO](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L243), 则服务端会回应一个`SERVER_HELLO`包, 其中包含了自己所监听的TCP端口
- 不论是广播的还是定向发送的, 客户端在收到`SERVER_HELLO`包后, 即可执行用户自定义的动作(比如直接就[连接](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L178)过去).
- 当客户端希望与所连接的服务端[断开连接](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L203)时, 它会先[构造一个DISCONNECT包](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L206)并[发送给服务端](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L207), 随后再[关闭](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L208)并[重建](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L210)自己的`tcp_socket`以便下次连接

## 3. Server
- 服务端在启动时会先试图[绑定一个TCP端口](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L225). 然后[构造SERVER_HELLO包](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L231)并[广播之](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L235)
- 在[accept()](https://github.com/TheMasterOfMagic/LearnSocket/blob/master/end.py#L288)中, 服务端会循环接受传入的连接, 并对每个传入的连接新开一个线程用于循环接受其发送的数据

## 4. 其他
- 在示例代码中,
	- 客户端在收到`SERVER_HELLO`时会直接连接目标服务端, 并随机发送若干`MESSAGE`包, 最后调用`disconnect()`与目标服务端断开连接. 期间每次发送时有一定几率直接退出, 不再给服务端任何消息(模拟客户端断线)
	- 服务端在收到`MESSAGE`包时, 有一定几率直接关闭套接字, 与目标客户端断开连接(模拟服务端断线)
- `server.py`与`client.py`中其实没有任何实质性内容. 这里是一个示范, 就是说如果这套框架真的被用起来, 那么用户程序员可以在`server.py`中编写一个`Server`的子类(比如`MyServer`), 然后自己实现`handle_tcp()`等关键函数, 即可在这套基于socket与多线程的局域网CS框架上做出自己想要的内容(比如多人联机小游戏或聊天室等)

# 体会与感悟
- 还记得大一小学期做小游戏时和小伙伴简单体验了下联机. 那会儿完全不会socket, 直到编写时才知道连接时要指定目标服务端的地址. 当时就问了老师"那一些联机游戏里不需要指定是怎么做到的?", 老师的回复是"等你学了socket就知道了"😂
- 当时是按下了这个问题没有去深究. 但当时后来又因为不会多线程, 搞得每次不发送信息就没法显示收到的信息(即便在发送之前已经收到了对方发送的信息). 后来知道了多线程, 再加上跟老师讨论了一下, 才知道这事儿就是另开一个线程去执行就好了(当时做小游戏时本来已经用到了多线程来刷新游戏画面, 但当时害怕把socket和多线程揉在一起所以没敢下手, 后来才知道其实没有当时想象的那么复杂)
- 包括这次这个项目, 其实我已开始是冲着聊天室去的. 但写着写着我发现过于注意聊天室的实现其实背离了我学习socket与多线程的初衷. 再加上我强迫症动不动从头写, 这个项目最后放上来的代码可能不到被删掉的代码的一半. 这也就是为什么最后它变成了一个框架, 而非一个具体的应用. 我希望掌握的, 或者说我通过这次项目可能部分掌握了的, 是这个"应用"里偏底层的通信机制, 而非这个"应用"本身的细节
- 虽然这个小项目只是对socket和多线程的一点初体验, 不过它确实为我打开了一个(或者说两个?)新世界的大门. 我这几百来行代码确实让我有种"学到了点能用一辈子的东西"的感觉
- 饿了, 吃饭了
