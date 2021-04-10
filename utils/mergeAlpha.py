import cv2
import os, sys


# 处理函数
def merge(img, img_alpha):
    try:
        b, g, r = cv2.split(img)
        img_mrg = cv2.merge((b, g, r, img_alpha))
        return [True, img_mrg, False]
    except:
        try:
            img_alpha = cv2.resize(img_alpha, (img_alpha.shape[0] * 2, img_alpha.shape[1] * 2))
            b, g, r = cv2.split(img)
            img_mrg = cv2.merge((b, g, r, img_alpha))
            return [True, img_mrg, "[alpha图层放大]"]
        except:
            return [False, False, False]


# 获取图像
def getimg(img_path, img_alpha_path):
    global alpha_alpha
    img = cv2.imread(img_path)
    if alpha_alpha is False:
        a = cv2.imread(img_alpha_path, cv2.IMREAD_GRAYSCALE)
    else:
        a = cv2.split(cv2.imread(img_alpha_path, cv2.IMREAD_UNCHANGED))[3]
    return img, a


# 获取目录内文件
def searchfileinfolder(folderpath='./', alpha_sig='[alpha]'):
    try:
        list = os.listdir(folderpath)
    except:
        return None
    success = []
    success_a = []
    for i in list:
        if alpha_sig in i:
            if i.replace(alpha_sig, '') in list:
                success.append(i.replace(alpha_sig, ''))
                success_a.append(i)
    return success, success_a


# 检查文件是否存在alpha图层
def checkfile(filename, alpha_sig='[alpha]'):
    if alpha_sig in filename:
        if os.path.isfile(filename.replace(alpha_sig, '')):
            return filename.replace(alpha_sig, ''), filename
        else:
            return False
    else:
        i_p = filename[:-4] + alpha_sig + filename[-4:]
        if os.path.isfile(i_p):
            return filename, i_p
        else:
            return False


if __name__ == '__main__':
    args = sys.argv
    if args.__len__() <= 1 or args.__len__() >= 5:
        print('将分离alpha的图像合成')
        print('\nUsage:%s [filename/filepath] alpha_sig alpha_alpha' % (args[0]))
        print('e.g. Arknights: %s dir/file [alpha] b\n\t\tor: %s dir/file' % (args[0], args[0]))
    else:
        print(str(args))
        if args.__len__() == 4:
            if args[3] == 'b':
                alpha_alpha = False
            elif args[3] == 'a':
                alpha_alpha = True
            else:
                print('except a(alpha_alpha) or b,but got %s' % args[3])
                exit(0)
            print('set:Alpha_alpha %s' % str(alpha_alpha))
        if args.__len__() >= 3:
            sig = args[2]
            alpha_alpha = False
        else:
            sig = '[alpha]'
            alpha_alpha = False
        print('set:<sig>%s' % sig)
        # 文件夹内文件合成
        if os.path.isdir(args[1]):
            print('set:<folder>%s' % args[1])
            img_p, a_p = searchfileinfolder(args[1], sig)
            print('get:%d file to merge' % img_p.__len__())
            if not os.path.isdir(str(args[1]) + '/merge/'):
                os.mkdir(str(args[1]) + '/merge/')
            for i in range(img_p.__len__()):
                try:
                    img_f = str(args[1]) + '/' + img_p[i]
                    alp_f = str(args[1]) + '/' + a_p[i]
                    m, a = getimg(img_f, alp_f)
                    img_m = merge(m, a)
                    if img_m[0]:
                        save_name = str(args[1]) + '/merge/' + img_p[i][:-4] + "_merge" + img_p[i][-4:]
                        cv2.imwrite(save_name, img_m[1])
                        if img_m[2] != False:
                            print("成功:%s%s" % (save_name, img_m[2]))
                        else:
                            print("成功:%s" % save_name)
                    else:
                        print("文件合成失败：%s [图像不匹配]" % img_p[i])
                except:
                    print("文件合成失败：%s[文件合成出现错误]" % img_p[i])
        # 文件合成
        elif os.path.isfile(args[1]):
            print('set:<file>%s' % args[1])
            if args.__len__() >= 3:
                print('set:<sig>%s' % args[2])
                m = checkfile(args[1], args[2])
            else:
                m = checkfile(args[1])
            if m == False:
                print('无效的文件%s' % args[1])
                os._exit(0)
            else:
                try:
                    i, a = getimg(m[0], m[1])
                    img_m = merge(i, a)
                    save_name = args[1][:-4] + "_merge" + args[1][-4:]
                    cv2.imwrite(save_name, img_m[1])
                    if img_m[2] != False:
                        print("成功:%s%s" % (save_name, img_m[2]))
                    else:
                        print("成功:%s" % save_name)
                except:
                    print("文件合成失败：%s" % args[1])
