from BigGAN_512 import BigGAN_512
from BigGAN_256 import BigGAN_256
from BigGAN_128 import BigGAN_128
import argparse
from utils import *

"""parsing and configuration"""
def parse_args():
    desc = "Tensorflow implementation of BigGAN"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--phase', type=str, default='train', help='train or test ?')
    # parser.add_argument('--dataset', type=str, default='celebA-HQ', help='[mnist / cifar10 / custom_dataset]')

    parser.add_argument('--epoch', type=int, default=50, help='The number of epochs to run')
    parser.add_argument('--iteration', type=int, default=10000, help='The number of training iterations')
    parser.add_argument('--batch_size', type=int, default=2048, help='The size of batch per gpu')
    parser.add_argument('--ch', type=int, default=96, help='base channel number per layer')

    # SAGAN
    # batch_size = 256
    # base channel = 64
    # epoch = 100 (1M iterations)

    parser.add_argument('--print_freq', type=int, default=1000, help='The number of image_print_freqy')
    parser.add_argument('--save_freq', type=int, default=1000, help='The number of ckpt_save_freq')

    parser.add_argument('--g_lr', type=float, default=0.00005, help='learning rate for generator')
    parser.add_argument('--d_lr', type=float, default=0.0002, help='learning rate for discriminator')

    # if lower batch size
    # g_lr = 0.0001
    # d_lr = 0.0004

    # if larger batch size
    # g_lr = 0.00005
    # d_lr = 0.0002

    parser.add_argument('--beta1', type=float, default=0.0, help='beta1 for Adam optimizer')
    parser.add_argument('--beta2', type=float, default=0.9, help='beta2 for Adam optimizer')
    parser.add_argument('--moving_decay', type=float, default=0.9999, help='moving average decay for generator')

    parser.add_argument('--z_dim', type=int, default=128, help='Dimension of noise vector')
    parser.add_argument('--sn', type=str2bool, default=True, help='using spectral norm')

    parser.add_argument('--gan_type', type=str, default='hinge', help='[gan / lsgan / wgan-gp / wgan-lp / dragan / hinge]')
    parser.add_argument('--ld', type=float, default=10.0, help='The gradient penalty lambda')

    parser.add_argument('--n_critic', type=int, default=2, help='The number of critic')

    parser.add_argument('--img_size', type=int, default=512, help='The size of image')
    parser.add_argument('--sample_num', type=int, default=64, help='The number of sample images')

    parser.add_argument('--test_num', type=int, default=10, help='The number of images generated by the test')

    parser.add_argument('--checkpoint_dir', type=str, default='checkpoint',
                        help='Directory name to save the checkpoints')
    parser.add_argument('--result_dir', type=str, default='results',
                        help='Directory name to save the generated images')
    parser.add_argument('--log_dir', type=str, default='logs',
                        help='Directory name to save training logs')
    parser.add_argument('--sample_dir', type=str, default='samples',
                        help='Directory name to save the samples on training')

    return check_args(parser.parse_args())

"""checking arguments"""
def check_args(args):
    # --checkpoint_dir
    check_folder(args.checkpoint_dir)

    # --result_dir
    check_folder(args.result_dir)

    # --result_dir
    check_folder(args.log_dir)

    # --sample_dir
    check_folder(args.sample_dir)

    # --epoch
    try:
        assert args.epoch >= 1
    except:
        print('number of epochs must be larger than or equal to one')

    # --batch_size
    try:
        assert args.batch_size >= 1
    except:
        print('batch size must be larger than or equal to one')
    return args


"""main"""
def main():
    # parse arguments
    args = parse_args()
    if args is None:
      exit()

    # open session
    with tf.Session(config=tf.ConfigProto(allow_soft_placement=True)) as sess:
        # default gan = BigGAN_128

        if args.img_size == 512 :
            gan = BigGAN_512(sess, args)
        elif args.img_size == 256 :
            gan = BigGAN_256(sess, args)
        else :
            gan = BigGAN_128(sess, args)

        # build graph
        gan.build_model()

        # show network architecture
        show_all_variables()

        if args.phase == 'train' :
            # launch the graph in a session
            gan.train()

            # visualize learned generator
            gan.visualize_results(args.epoch - 1)

            print(" [*] Training finished!")

        if args.phase == 'test' :
            gan.test()
            print(" [*] Test finished!")

if __name__ == '__main__':
    main()