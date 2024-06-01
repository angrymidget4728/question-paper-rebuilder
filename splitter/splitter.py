import fitz, os
from re import compile
from icecream import ic
from PIL import Image, ImageOps
from io import BytesIO

source_path = "source_files/4037_w12_qp_12.pdf"

# Converts PDF units to Image units at 300dpi
def scaled_to_image(pdf_page_width, pdf_coords):
    scale_factor = 2480 / pdf_page_width
    if type(pdf_coords) in {int, float}:
        return round(scale_factor * pdf_coords)
    if type(pdf_coords) in {list, tuple}:
        return [round(x * scale_factor) for x in pdf_coords]

# PDF page to bytes
def P2B(page): return BytesIO(page.get_pixmap(dpi=300).tobytes("png"))

class SplitQuestions:
    def __init__(self, filepath : str = source_path, local_source = True):
        # Assuming PDF is in local storage
        file_name = ""
        if local_source:
            file_name = os.path.splitext(os.path.split(filepath)[-1])[0]
        else:
            pass # Fetch URL header of PDF

        # Initialize primary variables
        source = fitz.open(filepath)
        paper_id_pattern = compile(r'\d{4}/\d{2}/[A-Z]/[A-Z]/\d{2}')
        start_page, page_num_elem, paper_id_elem, q1_elem, examiner_use_elem = self._get_first_page_info(source, paper_id_pattern)
        # All 'elem' variables store a tuple of information about piece of text in the PDF
        # E.g.: (topLeftX, topLeftY, bottomRightX, bottomRightY, text, blockNum, lineNum, wordNum)

        # ic(start_page, page_num_elem, paper_id_elem, q1_elem, examiner_use_elem)

        # Calculate the size of page,
        # the size of the gap between questions
        # the (image) coordinates of page number, left indentation (where question number exists), & right indentation (examiner's use)
        page_width, page_height = source[0].mediabox.width, source[0].mediabox.height
        one_line_gap = q1_elem[3] - q1_elem[1]
        one_line_gap_img = scaled_to_image(page_width, one_line_gap)
        page_num_tape = scaled_to_image(page_width, [0, page_num_elem[1], page_width, page_num_elem[3]])
        qp_num_tape = scaled_to_image(page_width, [0, paper_id_elem[3]-one_line_gap, page_width, paper_id_elem[3]+one_line_gap])
        examiner_use_tape = scaled_to_image(page_width, [examiner_use_elem[0]-one_line_gap/2, 0, page_width, page_height]) if examiner_use_elem else None

        white_pasties, either_or_location = self._get_white_tapes(source, start_page, page_num_tape, qp_num_tape, examiner_use_tape, page_width, page_height, one_line_gap)

        # Get list of whited out images (excluding either/or questions)
        self.taped_image_list = self._get_taped_image_list(source, white_pasties)

        # Append whited out either/or if available
        self.taped_image_list = self._get_taped_either_or(source, self.taped_image_list, either_or_location, one_line_gap_img)

        # Get list of question line slices
        self.sliced_image_list = self._get_sliced_image_list(self.taped_image_list, one_line_gap_img, page_width)

        # Get list of stitched questions
        self.stitched_image_list, right_bounds_image = self._get_stitched_image_list(self.sliced_image_list, page_width, q1_elem, one_line_gap_img)

        # Get stitched questions without question numbers (and maybe also include question paper numbers)
        self.stitched_image_list, self.question_number_coordinates, self.paper_id_strips = self._remove_questions_numbers(source, start_page, page_width, self.stitched_image_list, right_bounds_image, paper_id_elem, one_line_gap_img, len(either_or_location))

        # Save images
        self._save_split_images(file_name, self.stitched_image_list, self.paper_id_strips, len(either_or_location))


    # Find first page, store q1_elem and qnNumElem
    def _get_first_page_info(self, source, paper_id_pattern):
        start_page, page_num_elem, paper_id_elem, q1_elem, examiner_use_elem = None, None, None, None, None
        for page in source.pages(1):
            page_words = page.get_text('words')
            for word in page_words[1:25]:
                if not paper_id_elem and paper_id_pattern.match(word[4]):
                    paper_id_elem = word
                if not q1_elem and word[-1] == 0 and word[4] == '1' and word[2] < page.mediabox.width/8:
                    q1_elem, page_num_elem, start_page = word, page_words[0], page.number
                if not examiner_use_elem and 'Examiner' in word[4]:
                    examiner_use_elem = word
            if q1_elem and paper_id_elem: break
        
        return start_page, page_num_elem, paper_id_elem, q1_elem, examiner_use_elem
    
    # Store all the (image) locations that need to be blocked out by white 'tapes'
    def _get_white_tapes(self, file, startPage, pageNumTape, qpNumTape, examinerUseTape, pageWidth, pageHeight, oneLineGap):
        whitePasties = {}
        eitherOrLoc = []
        skipRemainingPages = False
        for page in file.pages(startPage):
            blankFound = False
            for block in page.get_text('blocks'):
                if 'BLANK PAGE' in block[4]: blankFound = True; break
            if blankFound: continue
            if skipRemainingPages: break
            pageWords = page.get_text('words')
            whitePasties[page.number] = []
            whitePasties[page.number].append(pageNumTape)
            whitePasties[page.number].append(qpNumTape)
            # if examinerUseElem: whitePasties[page.number].append(examinerUseTape)
            if examinerUseTape: whitePasties[page.number].append(examinerUseTape)
            for word in pageWords:
                if '......' in word[4] and word[2]-word[0]>pageWidth/2 and not '[' in word[4]:
                    whitePasties[page.number].append(scaled_to_image(pageWidth,word[:4]))
                if 'Section' in word[4] and word[0] / (pageWidth-word[2]) > 0.9:
                    whitePasties[page.number].append(scaled_to_image(pageWidth, [0,word[1],pageWidth,word[3]+oneLineGap*2]))
                if ('EITHER' in word[4] or 'OR' in word[4]):
                    if word[0]<pageWidth/4:
                        eitherOrLoc.append(scaled_to_image(pageWidth,word[:4])+[page.number]+[len(whitePasties)-1])
                    else:
                        whitePasties[page.number].append(scaled_to_image(pageWidth, [0,word[1]-oneLineGap*2,pageWidth,pageHeight]))
                        skipRemainingPages = True
                if 'Answer' in word[4] and word[-1] == 0:
                    whitePasties[page.number].append(scaled_to_image(pageWidth,[word[0],word[1],pageWidth,word[3]]))

            for block in page.get_text('blocks'):
                if 'Additional page' in block[4]:
                    whitePasties[page.number].append(scaled_to_image(pageWidth,[0,block[1],pageWidth,pageHeight]))
                    skipRemainingPages = True
                if page.number == len(file)-1 and not blankFound and "Permission to reproduce items" in block[4]:
                    whitePasties[page.number].append(scaled_to_image(pageWidth,[0,block[1]-oneLineGap,pageWidth,pageHeight]))
        
        return whitePasties, eitherOrLoc

    # Convert each page to image and 'paste' the white tapes
    def _get_taped_image_list(self, file, whitePasties):
        tapedImgList = []
        for k, v in whitePasties.items():
            pageImg = Image.open(P2B(file[k]))
            for _, x in enumerate(v):
                tape = Image.new('L', (x[2]-x[0], x[3]-x[1]), 255)
                pageImg.paste(tape, x)
            tapedImgList.append(pageImg)
        
        return tapedImgList

    def _get_taped_either_or(self, file, tapedImgList, eitherOrLoc, oneLineGapImg):
        if len(eitherOrLoc) > 0:
            eitherPageImg = Image.open(P2B(file[eitherOrLoc[0][-2]]))
            eitherQuesImg = eitherPageImg.crop([0,eitherOrLoc[0][1]-oneLineGapImg*2,eitherOrLoc[0][0],eitherOrLoc[0][3]+oneLineGapImg*2])
            eitherQuesBbox = ImageOps.invert(eitherQuesImg).getbbox()
            eitherQuesImgCropped = eitherQuesImg.crop(eitherQuesBbox)

            tapedImgList[eitherOrLoc[0][-1]].paste(Image.new('L',(eitherQuesImgCropped.width,eitherQuesImgCropped.height),255), (eitherQuesBbox[0], eitherOrLoc[0][1]-oneLineGapImg*2+eitherQuesBbox[1]))
            tapedImgList[eitherOrLoc[0][-1]].paste(eitherQuesImgCropped, (eitherQuesBbox[0], eitherOrLoc[0][1]+oneLineGapImg*2//10))
            tapedImgList[eitherOrLoc[1][-1]].paste(eitherQuesImgCropped, (eitherQuesBbox[0], eitherOrLoc[1][1]+oneLineGapImg*2//10))

        return tapedImgList
    
    # Slice up each page image into question block snippets
    def _get_sliced_image_list(self, tapedImgList, oneLineGapImg, pageWidth):
        slicedImgList = []
        checkHeight, pageWidthImg = int(oneLineGapImg*1.5), scaled_to_image(pageWidth, pageWidth)

        for img in tapedImgList:
            keepBox = [0,0,pageWidthImg,checkHeight]
            pixel = 0
            gapFoundBefore = False
            while pixel < img.height:
                checkBottom = pixel+checkHeight if pixel+checkHeight<img.height else img.height
                checkBox = ImageOps.invert(img.crop([0,pixel,pageWidthImg,checkBottom])).getbbox()
                if checkBox:
                    if not gapFoundBefore:
                        keepBox[3] = pixel+checkBox[3]
                        pixel += checkBox[3]
                    else:
                        keepBox[1], keepBox[3] = pixel+checkBox[1], pixel+checkBox[3]
                        gapFoundBefore = False
                        pixel += checkBox[1]
                else:
                    if not gapFoundBefore:
                        if pixel != 0 and not keepBox[3]-keepBox[1]<oneLineGapImg//2:
                            slicedImgList.append(img.crop(keepBox))
                        gapFoundBefore = True
                    pixel += checkHeight
                    keepBox[1], keepBox[3] = pixel, pixel
            if keepBox[3]-keepBox[1] != 0:
                slicedImgList.append(img.crop(keepBox))
        
        return slicedImgList
    
    def _get_stitched_image_list(self, slicedImgList, pageWidth, q1Elem, oneLineGapImg):
        stitchedImgList = []
        rBoundImg = scaled_to_image(pageWidth, q1Elem[2])
        for img in slicedImgList:
            potentialQuestion = ImageOps.invert(img.crop([0,0,rBoundImg,img.height])).getbbox()
            if potentialQuestion and oneLineGapImg//3 <= potentialQuestion[3]-potentialQuestion[1] <= oneLineGapImg:
                stitchedImgList.append(img)
            else:
                newImg = Image.new('L',(img.width,stitchedImgList[-1].height+oneLineGapImg), 255)
                newImg.paste(stitchedImgList[-1])
                stitchedImgList[-1] = newImg

                newImg = Image.new('L',(img.width,stitchedImgList[-1].height+img.height), 255)
                newImg.paste(stitchedImgList[-1])
                newImg.paste(img,(0,stitchedImgList[-1].height))
                stitchedImgList[-1] = newImg
        
        return stitchedImgList, rBoundImg
    
    def _remove_questions_numbers(self, file, startPage, pageWidth, stitchedImgList, rBoundImg, qpNumElem, oneLineGapImg, eitherOrExists=0):
        qCoordsList = []
        paperIdStrips = []
        whiteTape = Image.new('L', (rBoundImg+oneLineGapImg, int(oneLineGapImg*1.5)), 255)
        pageWidthImg = scaled_to_image(pageWidth, pageWidth)

        # Grab Paper ID
        paperIdGrabbedBlock = Image.open(P2B(file[startPage])).crop(scaled_to_image(pageWidth, qpNumElem[:4]))

        for idx, img in enumerate(stitchedImgList):
            # Grab Question Number
            croppedQuestionNum = img.crop((0, 0, rBoundImg+oneLineGapImg, int(oneLineGapImg*1.5)))
            croppedBoundBox = ImageOps.invert(croppedQuestionNum).getbbox()
            qCoordsList.append(croppedBoundBox)

            # Append question number to paper ID
            longStrip = Image.new('L', (pageWidthImg, oneLineGapImg*2), 255)
            longStrip.paste(croppedQuestionNum.crop(croppedBoundBox), (pageWidthImg-oneLineGapImg*2, int(oneLineGapImg*0.5)))
            longStrip.paste(paperIdGrabbedBlock, (pageWidthImg-oneLineGapImg*3-paperIdGrabbedBlock.width, int(oneLineGapImg*0.5)))

            # Hide question number
            img.paste(whiteTape)

            # Handle Either/Or
            if idx >= len(stitchedImgList)-2 and eitherOrExists > 0:
                eitherOrPart = img.crop((0, 0, pageWidthImg//2, oneLineGapImg))
                eitherOrPart = eitherOrPart.crop(ImageOps.invert(eitherOrPart).getbbox())
                longStrip.paste(eitherOrPart, (pageWidthImg-oneLineGapImg*4-paperIdGrabbedBlock.width-eitherOrPart.width, int(oneLineGapImg*0.5)))
                # longStrip.save(f"boss{idx}.png")

                questionPart = img.crop((0, oneLineGapImg, pageWidthImg, img.height))
                questionPart = questionPart.crop(ImageOps.invert(questionPart).getbbox())
                stitchedImgList[idx] = questionPart

            paperIdStrips.append(longStrip)
        
        return stitchedImgList, qCoordsList, paperIdStrips
    
    def _save_split_images(self, filename, image_list, strip_list, eitherOrExists=0):
        # filename = os.path.splitext(filename)[0]
        if not os.path.exists("exports"):
            os.makedirs("exports/questions")
            os.makedirs("exports/question_ids")
        for idx, (img, strip) in enumerate(zip(image_list, strip_list)):
            save_name = ""
            if idx < len(image_list)-2:
                save_name = f"{filename}_{idx+1}.png"
            else:
                if eitherOrExists > 0:
                    save_name = f"{filename}_{idx+1}E.png" if idx == len(image_list)-2 else f"{filename}_{idx}O.png"

            img.save(f"exports/questions/{save_name}")
            strip.save(f"exports/question_ids/{save_name}")




if __name__ == "__main__":
    boii = SplitQuestions()